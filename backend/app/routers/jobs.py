"""Polling endpoint for background jobs — see app/jobs/."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.jobs.service import get_job_for_user, job_progress_percent
from app.models.user import User
from app.schemas.job import JobStatusResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    job = await get_job_for_user(db, job_id=job_id, user_id=user.id)
    if job is None:
        raise ApiError(ErrorCode.NOT_FOUND, "No such job")
    progress = await job_progress_percent(db, job)
    return JobStatusResponse(
        id=str(job.id),
        type=job.type,
        status=job.status,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        progress_percent=progress,
        error=job.error,
        result=job.result,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
