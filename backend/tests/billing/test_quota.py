from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.billing.quota import PlanLimitNotConfigured, QuotaExceeded, check_and_reserve, release
from app.models.base import Base
from app.models.plan_limit import PlanLimit
from app.models.usage_counter import UsageCounter
from app.models.user import User


async def _create_user(db: AsyncSession, *, plan: str = "free") -> User:
    user = User(email=f"user-{id(object())}@example.com", full_name="Test User", plan=plan)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_check_and_reserve_succeeds_and_increments_used(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    reservation = await check_and_reserve(db_session, user=user, metric="ai_runs")
    assert reservation.amount == 1

    counter = (
        await db_session.execute(select(UsageCounter).where(UsageCounter.user_id == user.id))
    ).scalar_one()
    assert counter.used == 1
    assert counter.limit_snapshot == 20  # free/ai_runs seed value


async def test_check_and_reserve_raises_once_limit_is_reached(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    for _ in range(20):
        await check_and_reserve(db_session, user=user, metric="ai_runs")

    with pytest.raises(QuotaExceeded) as excinfo:
        await check_and_reserve(db_session, user=user, metric="ai_runs")

    error = excinfo.value
    assert error.metric == "ai_runs"
    assert error.used == 20
    assert error.limit == 20
    assert error.window == "day"
    assert error.upgrade_required is True
    assert error.code.value == "QUOTA_EXCEEDED"
    assert error.status_code == 402


async def test_pro_plan_denial_does_not_suggest_upgrade(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, plan="pro")
    for _ in range(500):
        await check_and_reserve(db_session, user=user, metric="ai_runs")
    with pytest.raises(QuotaExceeded) as excinfo:
        await check_and_reserve(db_session, user=user, metric="ai_runs")
    assert excinfo.value.upgrade_required is False


async def test_release_gives_back_a_reservation(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    reservation = await check_and_reserve(db_session, user=user, metric="ai_runs")
    await release(db_session, reservation)

    counter = (
        await db_session.execute(select(UsageCounter).where(UsageCounter.user_id == user.id))
    ).scalar_one()
    assert counter.used == 0


async def test_missing_plan_limit_raises(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    with pytest.raises(PlanLimitNotConfigured):
        await check_and_reserve(db_session, user=user, metric="no_such_metric")


async def test_concurrent_requests_never_exceed_the_limit() -> None:
    """50 simultaneous reservations against a limit of 10 -- exactly 10
    must succeed. This is the whole point of doing the increment and the
    limit check as one atomic statement rather than read-then-write."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_maker() as setup:
        user = User(email="racer@example.com", full_name="Racer", plan="free")
        setup.add(user)
        setup.add(
            PlanLimit(
                plan="free",
                metric="concurrency_test",
                limit_value=10,
                window="day",
                overage_behaviour="block",
            )
        )
        await setup.commit()
        await setup.refresh(user)
        user_id = user.id

    async def attempt() -> bool:
        async with session_maker() as session:
            user = await session.get(User, user_id)
            assert user is not None
            try:
                await check_and_reserve(session, user=user, metric="concurrency_test")
                return True
            except QuotaExceeded:
                return False

    results = await asyncio.gather(*(attempt() for _ in range(50)))
    assert sum(results) == 10

    async with session_maker() as verify:
        counter = (
            await verify.execute(
                select(UsageCounter).where(
                    UsageCounter.user_id == user_id, UsageCounter.metric == "concurrency_test"
                )
            )
        ).scalar_one()
        assert counter.used == 10

    await engine.dispose()


async def test_period_boundaries_are_computed_correctly(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    reservation = await check_and_reserve(db_session, user=user, metric="ai_runs")
    now = datetime.now(UTC)
    assert reservation.period_start <= now
    assert reservation.period_start.hour == 0
    counter = (
        await db_session.execute(select(UsageCounter).where(UsageCounter.user_id == user.id))
    ).scalar_one()
    assert counter.period_end - counter.period_start == timedelta(days=1)
