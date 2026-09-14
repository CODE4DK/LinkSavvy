from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.notifications import service


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"notif-{uuid.uuid4()}@example.com", full_name="Notif Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_create_notification_respects_in_app_preference(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await service.set_preference(
        db_session,
        user_id=user.id,
        channel="in_app",
        notification_type="product.update",
        enabled=False,
    )

    created = await service.create_notification(
        db_session,
        user_id=user.id,
        notification_type="product.update",
        title="New feature",
        body="We shipped something",
    )
    assert created is None

    page = await service.list_notifications(db_session, user_id=user.id)
    assert page.items == []


async def test_create_notification_default_enabled_with_no_preference_row(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    created = await service.create_notification(
        db_session,
        user_id=user.id,
        notification_type="audit.completed",
        title="Audit ready",
        body="Your audit finished",
        action_route="/dashboard",
    )
    assert created is not None
    page = await service.list_notifications(db_session, user_id=user.id)
    assert page.unread_count == 1
    assert page.items[0].title == "Audit ready"


async def test_mark_read_and_mark_all_read(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    for i in range(3):
        await service.create_notification(
            db_session,
            user_id=user.id,
            notification_type="product.update" if i else "audit.completed",
            title=f"n{i}",
            body="body",
        )
    # product.update defaults to email-off but in_app stays on, so all
    # three should have been created.
    page = await service.list_notifications(db_session, user_id=user.id)
    assert page.unread_count == 3

    await service.mark_read(db_session, user_id=user.id, notification_id=page.items[0].id)
    page = await service.list_notifications(db_session, user_id=user.id)
    assert page.unread_count == 2

    marked = await service.mark_all_read(db_session, user_id=user.id)
    assert marked == 2
    page = await service.list_notifications(db_session, user_id=user.id)
    assert page.unread_count == 0


async def test_mark_read_rejects_another_users_notification(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session)
    other = await _create_user(db_session)
    notification = await service.create_notification(
        db_session, user_id=owner.id, notification_type="audit.completed", title="t", body="b"
    )
    assert notification is not None
    try:
        await service.mark_read(db_session, user_id=other.id, notification_id=notification.id)
        raise AssertionError("expected NotificationNotFound")
    except service.NotificationNotFound:
        pass


async def test_list_preferences_defaults_product_update_email_off(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    rows = await service.list_preferences(db_session, user_id=user.id)
    by_key = {(channel, t): enabled for channel, t, enabled in rows}
    assert by_key[("email", "product.update")] is False
    assert by_key[("in_app", "product.update")] is True
    assert by_key[("email", "audit.completed")] is True


async def test_set_preference_overrides_default(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await service.set_preference(
        db_session,
        user_id=user.id,
        channel="email",
        notification_type="product.update",
        enabled=True,
    )
    assert await service.channel_enabled(
        db_session, user_id=user.id, channel="email", notification_type="product.update"
    )
