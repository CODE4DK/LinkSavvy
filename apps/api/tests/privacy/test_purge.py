from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError
from app.models.ai_cache import AICache
from app.models.ai_invocation import AIInvocation
from app.models.asset import Asset
from app.models.profile_import import ProfileImportBlob
from app.models.subscription import Subscription
from app.models.user import User
from app.privacy import purge
from app.settings import settings


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(email=f"purge-{uuid.uuid4()}@example.com", full_name="Purge Tester", **kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_hard_delete_user_removes_owned_rows_and_the_user_itself(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, billing_country="US")
    db_session.add(Asset(user_id=user.id, type="post", title="t", body="b", tags=[]))
    await db_session.commit()

    await purge.hard_delete_user(db_session, user_id=user.id)

    assert await db_session.get(User, user.id) is None
    remaining_assets = (
        (await db_session.execute(select(Asset).where(Asset.user_id == user.id))).scalars().all()
    )
    assert remaining_assets == []


async def test_hard_delete_user_deletes_provider_customer(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, billing_country="US")
    db_session.add(
        Subscription(
            user_id=user.id,
            provider="stripe",
            plan="pro",
            provider_customer_id="cus_to_delete",
        )
    )
    await db_session.commit()

    # FakeProvider.delete_customer is a no-op that never raises -- this
    # just proves hard_delete_user doesn't blow up calling it and still
    # deletes the local rows afterward.
    await purge.hard_delete_user(db_session, user_id=user.id)
    assert await db_session.get(User, user.id) is None


async def test_hard_delete_user_404s_for_an_unknown_user(db_session: AsyncSession) -> None:
    try:
        await purge.hard_delete_user(db_session, user_id=uuid.uuid4())
        raise AssertionError("expected ApiError")
    except ApiError as exc:
        assert exc.code.value == "NOT_FOUND"


async def test_purge_expired_profile_imports(db_session: AsyncSession) -> None:
    db_session.add(
        ProfileImportBlob(
            ciphertext=b"secret",
            content_type="text/plain",
            expires_at=datetime.now(UTC) - timedelta(days=1),
            created_at=datetime.now(UTC) - timedelta(days=31),
        )
    )
    db_session.add(
        ProfileImportBlob(
            ciphertext=b"secret2",
            content_type="text/plain",
            expires_at=datetime.now(UTC) + timedelta(days=10),
            created_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    purged = await purge.purge_expired_profile_imports(db_session)
    assert purged == 1
    remaining = (await db_session.execute(select(ProfileImportBlob))).scalars().all()
    assert len(remaining) == 1


async def test_purge_expired_ai_cache(db_session: AsyncSession) -> None:
    db_session.add(
        AICache(
            cache_key="expired-key",
            prompt_id="test.prompt",
            prompt_version=1,
            response={"reply": "hi"},
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
    )
    db_session.add(
        AICache(
            cache_key="fresh-key",
            prompt_id="test.prompt",
            prompt_version=1,
            response={"reply": "hi"},
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    await db_session.commit()

    purged = await purge.purge_expired_ai_cache(db_session)
    assert purged == 1


async def test_purge_old_ai_invocations(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)

    def _invocation(*, created_at: datetime) -> AIInvocation:
        return AIInvocation(
            user_id=user.id,
            prompt_id="test.prompt",
            prompt_version=1,
            tier="standard",
            provider="fake",
            model="fake-model",
            outcome="ok",
            correlation_id=str(uuid.uuid4()),
            created_at=created_at,
        )

    db_session.add(
        _invocation(
            created_at=datetime.now(UTC)
            - timedelta(days=settings.ai_invocation_payload_retention_days + 1)
        )
    )
    db_session.add(_invocation(created_at=datetime.now(UTC)))
    await db_session.commit()

    purged = await purge.purge_old_ai_invocations(db_session)
    assert purged == 1
    remaining = (await db_session.execute(select(AIInvocation))).scalars().all()
    assert len(remaining) == 1


async def test_find_users_due_for_hard_delete(db_session: AsyncSession) -> None:
    overdue = await _create_user(db_session)
    overdue.status = "deleted"
    overdue.deleted_at = datetime.now(UTC) - timedelta(
        days=settings.account_hard_delete_after_days + 1
    )
    recent = await _create_user(db_session)
    recent.status = "deleted"
    recent.deleted_at = datetime.now(UTC)
    await db_session.commit()

    due = await purge.find_users_due_for_hard_delete(db_session)
    assert overdue.id in due
    assert recent.id not in due
