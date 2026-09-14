"""Platform health: job queue depth, dead-lettered jobs with a retry
control, and each AI provider's circuit-breaker state."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.circuit_breaker import circuit_breaker
from app.errors import ApiError, ErrorCode
from app.models.job import Job
from app.services.audit import record_audit_event


@dataclass(frozen=True, slots=True)
class QueueDepth:
    queued: int
    leased: int
    dead: int
    failed_last_hour: int


async def queue_depth(db: AsyncSession) -> QueueDepth:
    rows = (await db.execute(select(Job.status, func.count()).group_by(Job.status))).all()
    counts: dict[str, int] = {status: int(count) for status, count in rows}
    failed_last_hour = (
        await db.execute(
            select(func.count()).where(
                Job.status == "failed",
                Job.finished_at >= datetime.now(UTC) - timedelta(hours=1),
            )
        )
    ).scalar_one()
    return QueueDepth(
        queued=int(counts.get("queued", 0)),
        leased=int(counts.get("leased", 0)),
        dead=int(counts.get("dead", 0)),
        failed_last_hour=int(failed_last_hour),
    )


async def list_dead_jobs(db: AsyncSession, *, limit: int = 50) -> list[Job]:
    return list(
        (
            await db.execute(
                select(Job)
                .where(Job.status == "dead")
                .order_by(Job.finished_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )


async def retry_dead_job(db: AsyncSession, *, admin_id: uuid.UUID, job_id: uuid.UUID) -> Job:
    job = await db.get(Job, job_id)
    if job is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such job")
    if job.status != "dead":
        raise ApiError(ErrorCode.VALIDATION_FAILED, "only a dead job can be retried")

    job.status = "queued"
    job.attempts = 0
    job.error = None
    job.lease_expires_at = None
    job.worker_id = None
    job.scheduled_for = datetime.now(UTC)
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.job.retry",
        target_type="job",
        target_id=str(job_id),
    )
    await db.commit()
    await db.refresh(job)
    return job


def provider_circuit_state() -> dict[str, dict[str, object]]:
    return circuit_breaker.snapshot()
