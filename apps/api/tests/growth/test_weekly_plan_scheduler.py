from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.weekly_plan_scheduler import is_due, run_once
from app.models.job import Job
from app.models.user import User

_A_MONDAY_AT_SIX_UTC = datetime(2026, 9, 14, 6, 0, tzinfo=UTC)
_A_TUESDAY_UTC = datetime(2026, 9, 15, 6, 0, tzinfo=UTC)


async def _create_user(db: AsyncSession, *, timezone: str = "UTC") -> User:
    user = User(
        email=f"growth-sched-{uuid.uuid4()}@example.com",
        full_name="Scheduler Tester",
        timezone=timezone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def test_is_due_only_on_monday_near_six_am() -> None:
    assert is_due(datetime(2026, 9, 14, 6, 0))  # a Monday
    assert is_due(datetime(2026, 9, 14, 6, 25))
    assert not is_due(datetime(2026, 9, 14, 7, 0))
    assert not is_due(datetime(2026, 9, 15, 6, 0))  # a Tuesday


async def test_enqueues_a_job_when_a_users_local_time_is_due(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, timezone="UTC")

    enqueued = await run_once(db_session, now_utc=_A_MONDAY_AT_SIX_UTC)

    assert enqueued == 1
    result = await db_session.execute(select(Job).where(Job.user_id == user.id))
    jobs = result.scalars().all()
    assert len(jobs) == 1
    assert jobs[0].type == "weekly_plan.generate"


async def test_skips_users_not_yet_due(db_session: AsyncSession) -> None:
    await _create_user(db_session, timezone="UTC")

    enqueued = await run_once(db_session, now_utc=_A_TUESDAY_UTC)

    assert enqueued == 0


async def test_does_not_enqueue_twice_for_the_same_week(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, timezone="UTC")

    first = await run_once(db_session, now_utc=_A_MONDAY_AT_SIX_UTC)
    second = await run_once(db_session, now_utc=_A_MONDAY_AT_SIX_UTC.replace(minute=20))

    assert first == 1
    assert second == 0
    result = await db_session.execute(select(Job).where(Job.user_id == user.id))
    assert len(result.scalars().all()) == 1


async def test_respects_each_users_own_timezone(db_session: AsyncSession) -> None:
    # 06:00 UTC is 22:00 the previous day in Los Angeles -- not due there.
    la_user = await _create_user(db_session, timezone="America/Los_Angeles")

    enqueued = await run_once(db_session, now_utc=_A_MONDAY_AT_SIX_UTC)

    assert enqueued == 0
    result = await db_session.execute(select(Job).where(Job.user_id == la_user.id))
    assert result.scalars().all() == []


async def test_ignores_users_with_an_unrecognised_timezone(db_session: AsyncSession) -> None:
    await _create_user(db_session, timezone="Not/A_Real_Zone")

    enqueued = await run_once(db_session, now_utc=_A_MONDAY_AT_SIX_UTC)

    assert enqueued == 0
