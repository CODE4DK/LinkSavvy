"""Enqueues `notifications.weekly_digest` per user -- the same
"separate polling loop rather than a job-table concept" shape as
app/growth/weekly_plan_scheduler.py, offset an hour later so a user's
digest email reports on a plan that's actually finished generating.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, SessionFactory
from app.jobs.queue import enqueue
from app.models.job import Job
from app.models.user import User
from app.notifications.weekly_digest_job import WEEKLY_DIGEST_JOB_TYPE

logger = logging.getLogger("app.notifications.weekly_digest_scheduler")

_TARGET_HOUR = 7  # one hour after weekly_plan_scheduler's Monday 06:00
_TOLERANCE_MINUTES = 30
DEFAULT_POLL_INTERVAL_SECONDS = 300.0


def is_due(now_local: datetime) -> bool:
    if now_local.weekday() != 0:  # Monday
        return False
    target_minutes = _TARGET_HOUR * 60
    now_minutes = now_local.hour * 60 + now_local.minute
    return abs(now_minutes - target_minutes) <= _TOLERANCE_MINUTES


async def _already_enqueued_this_week(db: AsyncSession, *, user: User, week_start: date) -> bool:
    result = await db.execute(
        select(Job.id).where(
            Job.user_id == user.id,
            Job.type == WEEKLY_DIGEST_JOB_TYPE,
            Job.status.not_in(("failed", "dead")),
            Job.created_at >= datetime.combine(week_start, datetime.min.time(), tzinfo=UTC),
        )
    )
    return result.first() is not None


async def run_once(db: AsyncSession, *, now_utc: datetime | None = None) -> int:
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
        await enqueue(db, job_type=WEEKLY_DIGEST_JOB_TYPE, payload={}, user_id=user.id)
        enqueued += 1
    return enqueued


async def run_scheduler(
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    iterations: int | None = None,
    session_factory: SessionFactory = AsyncSessionLocal,
) -> None:
    count = 0
    while iterations is None or count < iterations:
        async with session_factory() as db:
            enqueued = await run_once(db)
            if enqueued:
                logger.info("weekly_digest_scheduler_enqueued", extra={"count": enqueued})
        count += 1
        if iterations is None or count < iterations:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_scheduler())
