from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.billing import period_sweep, service
from app.billing.providers.base import NormalisedEvent, NormalisedEventType
from app.billing.providers.fake import queue_event
from app.models.asset import Asset
from app.models.subscription import Subscription
from app.models.user import User
from app.models.webhook_event import WebhookEvent


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(email=f"billing-{uuid.uuid4()}@example.com", full_name="Billing Tester", **kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_get_or_create_subscription_routes_india_to_razorpay(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, billing_country="IN")
    subscription = await service.get_or_create_subscription(db_session, user=user)
    assert subscription.provider == "razorpay"
    assert subscription.plan == "free"


async def test_get_or_create_subscription_is_idempotent(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, billing_country="US")
    first = await service.get_or_create_subscription(db_session, user=user)
    second = await service.get_or_create_subscription(db_session, user=user)
    assert first.id == second.id
    assert first.provider == "stripe"


async def test_get_or_create_subscription_recovers_from_a_concurrent_insert(
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Regression test for a real 500 (sqlalchemy.exc.MultipleResultsFound)
    this phase's E2E pass hit on a real account: get_or_create_subscription
    is a select-then-insert with nothing but its own SELECT protecting it,
    so two concurrent first-ever calls for the same user could each insert
    their own row.

    True asyncio-concurrency against a single shared in-memory SQLite
    connection (the shape tests/jobs/test_worker.py uses for its own
    concurrent-lease test) deadlocks here instead of racing, because this
    function's path is a multi-statement transaction rather than one
    atomic UPDATE. So this reproduces the failure mode deterministically
    instead, by patching this db_session's own commit() -- the one await
    point between the function's SELECT (already run, found nothing) and
    its INSERT actually landing -- to run a second, independent session's
    full get_or_create_subscription call for the same user first. That's
    exactly "another request's call completes in between", without
    needing real concurrency. uq_subscriptions_user_id (migration 0022)
    plus the IntegrityError fallback in the function under test should
    then make this call resolve to the other session's row instead of
    raising.
    """
    user = await _create_user(db_session, billing_country="US")
    user_id = user.id

    real_commit = db_session.commit
    winner_id_box: list[uuid.UUID] = []

    async def _commit_after_a_concurrent_winner() -> None:
        async with db_sessionmaker() as other_session:
            other_user = await other_session.get(User, user_id)
            assert other_user is not None
            winner = await service.get_or_create_subscription(other_session, user=other_user)
            winner_id_box.append(winner.id)
        await real_commit()

    db_session.commit = _commit_after_a_concurrent_winner  # type: ignore[method-assign]

    result = await service.get_or_create_subscription(db_session, user=user)

    assert winner_id_box == [result.id]


def _activated_event(*, event_id: str, user_id: uuid.UUID, period_end: datetime) -> NormalisedEvent:
    return NormalisedEvent(
        type=NormalisedEventType.SUBSCRIPTION_ACTIVATED,
        provider_event_id=event_id,
        provider_subscription_id="sub_123",
        provider_customer_id="cus_123",
        status="active",
        plan="pro",
        interval="month",
        current_period_start=datetime.now(UTC),
        current_period_end=period_end,
        currency="usd",
        amount_minor=2900,
        user_id_hint=str(user_id),
    )


async def test_webhook_activates_subscription_and_grants_entitlements(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, billing_country="US")
    period_end = datetime.now(UTC) + timedelta(days=30)
    event = _activated_event(event_id="evt_1", user_id=user.id, period_end=period_end)
    queue_event(event)

    record = await service.process_webhook_event(
        db_session,
        provider_name="stripe",
        headers={"x-fake-event-id": "evt_1"},
        body=b"{}",
    )
    assert record.status == "processed"

    await db_session.refresh(user)
    assert user.plan == "pro"

    subscription = await service.get_or_create_subscription(db_session, user=user)
    assert subscription.status == "active"
    assert subscription.provider_subscription_id == "sub_123"
    assert subscription.current_period_end is not None


async def test_replayed_webhook_is_a_no_op(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, billing_country="US")
    period_end = datetime.now(UTC) + timedelta(days=30)
    event = _activated_event(event_id="evt_replay", user_id=user.id, period_end=period_end)
    queue_event(event)
    headers = {"x-fake-event-id": "evt_replay"}

    first = await service.process_webhook_event(
        db_session, provider_name="stripe", headers=headers, body=b"{}"
    )
    second = await service.process_webhook_event(
        db_session, provider_name="stripe", headers=headers, body=b"{}"
    )
    assert first.id == second.id

    count = (
        await db_session.execute(
            WebhookEvent.__table__.select().where(WebhookEvent.provider_event_id == "evt_replay")
        )
    ).fetchall()
    assert len(count) == 1


async def test_out_of_order_renewal_does_not_roll_back_period_end(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, billing_country="US")
    later_end = datetime.now(UTC) + timedelta(days=30)
    queue_event(_activated_event(event_id="evt_a", user_id=user.id, period_end=later_end))
    await service.process_webhook_event(
        db_session, provider_name="stripe", headers={"x-fake-event-id": "evt_a"}, body=b"{}"
    )

    stale_renewal = NormalisedEvent(
        type=NormalisedEventType.SUBSCRIPTION_RENEWED,
        provider_event_id="evt_b_late",
        provider_subscription_id="sub_123",
        current_period_start=datetime.now(UTC) - timedelta(days=60),
        current_period_end=datetime.now(UTC) - timedelta(days=30),  # older than what's stored
    )
    queue_event(stale_renewal)
    await service.process_webhook_event(
        db_session, provider_name="stripe", headers={"x-fake-event-id": "evt_b_late"}, body=b"{}"
    )

    subscription = await service.get_or_create_subscription(db_session, user=user)
    assert subscription.current_period_end == later_end


async def test_downgrade_freezes_overflow_assets_without_deleting_them(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, billing_country="US")
    user.plan = "pro"
    await db_session.commit()

    for i in range(25):
        db_session.add(Asset(user_id=user.id, type="post", title=f"post {i}", body="body", tags=[]))
    await db_session.commit()

    from app.billing.entitlements import FREE_ASSET_STORAGE_CAP, apply_entitlements

    await apply_entitlements(db_session, user=user, plan="free")
    await db_session.commit()

    result = await db_session.execute(Asset.__table__.select().where(Asset.user_id == user.id))
    rows = result.fetchall()
    assert len(rows) == 25  # nothing deleted
    read_only_count = sum(1 for row in rows if row.read_only)
    assert read_only_count == 25 - FREE_ASSET_STORAGE_CAP

    await apply_entitlements(db_session, user=user, plan="pro")
    await db_session.commit()
    result = await db_session.execute(Asset.__table__.select().where(Asset.user_id == user.id))
    assert all(not row.read_only for row in result.fetchall())


async def test_period_sweep_downgrades_expired_cancelled_subscription(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, billing_country="US")
    user.plan = "pro"
    await db_session.commit()
    subscription = Subscription(
        user_id=user.id,
        provider="stripe",
        plan="pro",
        status="cancelled",
        current_period_end=datetime.now(UTC) - timedelta(days=1),
    )
    db_session.add(subscription)
    await db_session.commit()

    downgraded = await period_sweep.run_once(db_session)
    assert downgraded == 1

    await db_session.refresh(user)
    assert user.plan == "free"
