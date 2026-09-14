from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import subscriptions as admin_subscriptions
from app.billing.providers.base import NormalisedEvent, NormalisedEventType
from app.billing.providers.fake import queue_event
from app.billing.service import get_or_create_subscription, process_webhook_event
from app.models.user import User


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(email=f"admin-sub-{uuid.uuid4()}@example.com", full_name="Sub Tester", **kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_list_subscriptions_filters_by_status(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, billing_country="US")
    await get_or_create_subscription(db_session, user=user)

    active = await admin_subscriptions.list_subscriptions(db_session, status="trialing")
    assert any(s.user_id == user.id for s in active.items)

    none_cancelled = await admin_subscriptions.list_subscriptions(db_session, status="cancelled")
    assert not any(s.user_id == user.id for s in none_cancelled.items)


async def test_replay_webhook_reprocesses_a_failed_event(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    user = await _create_user(db_session, billing_country="US")

    event = NormalisedEvent(
        type=NormalisedEventType.SUBSCRIPTION_ACTIVATED,
        provider_event_id="evt_replay_1",
        provider_subscription_id="sub_replay_1",
        status="active",
        plan="pro",
        interval="month",
        current_period_end=datetime.now(UTC) + timedelta(days=30),
        user_id_hint=str(user.id),
        # FakeProvider.parse_payload looks the queued event back up by this
        # key (a real provider's stored payload naturally carries its own
        # event id inside it; the fake needs it spelled out explicitly).
        raw={"provider_event_id": "evt_replay_1"},
    )
    queue_event(event)
    record = await process_webhook_event(
        db_session,
        provider_name="stripe",
        headers={"x-fake-event-id": "evt_replay_1"},
        body=b"{}",
    )
    assert record.status == "processed"

    replayed = await admin_subscriptions.replay_webhook(
        db_session, admin_id=admin.id, webhook_event_id=record.id
    )
    assert replayed.status == "processed"
    assert replayed.attempts == 2
