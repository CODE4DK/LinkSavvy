"""The `weekly_plan.generate` job: enqueued per-user by
app.growth.weekly_plan_scheduler, executed by the ordinary job worker.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.growth.weekly_plan import generate_plan_for_user
from app.jobs.registry import register_handler
from app.models.job import Job
from app.models.user import User

WEEKLY_PLAN_JOB_TYPE = "weekly_plan.generate"


@register_handler(WEEKLY_PLAN_JOB_TYPE)
async def generate_weekly_plan(
    job: Job, db: AsyncSession, session_factory: SessionFactory
) -> dict[str, Any] | None:
    user = await db.get(User, job.user_id)
    if user is None or user.deleted_at is not None:
        return {"skipped": "user no longer exists"}

    plan = await generate_plan_for_user(db, user=user)
    return {
        "weekly_plan_id": str(plan.id),
        "week_start": plan.week_start.isoformat(),
        "item_count": len(plan.items),
    }
