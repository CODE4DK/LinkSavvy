"""Detects "it's Monday 06:00 in this user's timezone" and enqueues a
`weekly_plan.generate` job -- a separate lightweight polling process
rather than a change to the jobs table's schema. Every `Job` row needs a
real owning `user_id`; a per-user weekly trigger has one once it fires,
but nothing in the jobs table represents "run this for every user on a
schedule", and adding that concept there would touch a table every other
job type also depends on for one feature's benefit. See docs/adr/0009.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, SessionFactory
from app.growth.weekly_plan_job import WEEKLY_PLAN_JOB_TYPE
from app.jobs.queue import enqueue
from app.models.job import Job
from app.models.user import User

logger = logging.getLogger("app.growth.weekly_plan_scheduler")

_TARGET_HOUR = 6
_TOLERANCE_MINUTES = 30
DEFAULT_POLL_INTERVAL_SECONDS = 300.0


def is_due(now_local: datetime) -> bool:
    if now_local.weekday() != 0:  # Monday
        return False
    target_minutes = _TARGET_HOUR * 60
    now_minutes = now_local.hour * 60 + now_local.minute
    return abs(now_minutes - target_minutes) <= _TOLERANCE_MINUTES


async def _already_enqueued_this_week(db: AsyncSession, *, user: User, week_start: date) -> bool:
    """Dedup on the `Job` row, not on `WeeklyPlan` -- the plan itself
    doesn't exist until the worker actually runs the job, which can be
    minutes behind a busy scheduler, and checking WeeklyPlan would let a
    second poll enqueue a duplicate before the first job even starts.
    `week_start` is compared in Python (not a JSON path in SQL) so this
    works identically against MySQL and the SQLite test database."""
    result = await db.execute(
        select(Job.payload).where(
            Job.user_id == user.id,
            Job.type == WEEKLY_PLAN_JOB_TYPE,
            Job.status.not_in(("failed", "dead")),
        )
    )
    target = week_start.isoformat()
    return any(payload.get("week_start") == target for payload in result.scalars().all())


async def run_once(db: AsyncSession, *, now_utc: datetime | None = None) -> int:
    """Checks every active user once; returns how many jobs it enqueued.
    `now_utc` is an injection seam for tests -- production always leaves
    it as the real current time."""
    reference = now_utc if now_utc is not None else datetime.now(UTC)
    enqueued = 0
    result = await db.execute(
        select(User).where(User.deleted_at.is_(None), User.status == "active")
    )
    for user in result.scalars().all():
        try:
            tz = ZoneInfo(user.timezone)
        except ZoneInfoNotFoundError:
            continue
        now_local = reference.astimezone(tz)
        if not is_due(now_local):
            continue
        week_start = (now_local - timedelta(days=now_local.weekday())).date()
        if await _already_enqueued_this_week(db, user=user, week_start=week_start):
            continue
        await enqueue(
            db,
            job_type=WEEKLY_PLAN_JOB_TYPE,
            payload={"week_start": week_start.isoformat()},
            user_id=user.id,
        )
        enqueued += 1
    return enqueued


async def run_scheduler(
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    iterations: int | None = None,
    session_factory: SessionFactory = AsyncSessionLocal,
) -> None:
    """The long-running loop. `iterations=None` runs forever (real
    deployment); a finite `iterations` is what tests pass to run a
    bounded number of poll cycles."""
    count = 0
    while iterations is None or count < iterations:
        async with session_factory() as db:
            enqueued = await run_once(db)
            if enqueued:
                logger.info("weekly_plan_scheduler_enqueued", extra={"count": enqueued})
        count += 1
        if iterations is None or count < iterations:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_scheduler())
