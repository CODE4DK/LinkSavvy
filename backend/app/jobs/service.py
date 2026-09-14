"""Read-side helpers backing GET /api/v1/jobs/{id}."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.registry import compute_progress
from app.models.job import Job


async def get_job_for_user(
    db: AsyncSession, *, job_id: uuid.UUID, user_id: uuid.UUID
) -> Job | None:
    job = await db.get(Job, job_id)
    if job is None or job.user_id != user_id:
        return None
    return job


async def job_progress_percent(db: AsyncSession, job: Job) -> int:
    return await compute_progress(job, db)
