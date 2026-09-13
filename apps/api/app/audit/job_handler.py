"""Registers the `"audit"` job type against the background job runner
(app/jobs/) -- `POST /api/v1/audits` enqueues one of these rather than
running the orchestrator inline, so a slow category never blocks the
request. The API layer is expected to have already validated quota and
that the user has an active profile snapshot before enqueueing; the
errors raised here are defensive, not the normal path.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.orchestrator import run_audit
from app.content.content_history import resolve_content_history
from app.db import SessionFactory
from app.jobs.registry import register_handler, register_progress_calculator
from app.models.audit import Audit, AuditCategoryResult
from app.models.job import Job
from app.models.user import User
from app.profiles.service import get_active_snapshot

_CATEGORY_COUNT = 5
# Reserve the first 10% for "leased, orchestrator hasn't created the Audit
# row yet" and spread the rest evenly across the five categories finishing.
_BASE_PERCENT = 10
_PER_CATEGORY_PERCENT = (100 - _BASE_PERCENT) // _CATEGORY_COUNT


@register_handler("audit")
async def run_audit_job(
    job: Job, db: AsyncSession, session_factory: SessionFactory
) -> dict[str, Any]:
    user = await db.get(User, job.user_id)
    if user is None:
        raise RuntimeError(f"audit job {job.id}: user {job.user_id} not found")

    snapshot_row = await get_active_snapshot(db, user_id=job.user_id)
    if snapshot_row is None:
        raise RuntimeError(f"audit job {job.id}: user {job.user_id} has no active profile snapshot")

    content_history = await resolve_content_history(
        db, user_id=job.user_id, explicit=job.payload.get("content_history")
    )
    audit = await run_audit(
        user=user,
        db=db,
        snapshot_row=snapshot_row,
        trigger=job.payload.get("trigger", "manual"),
        target_role=job.payload.get("target_role"),
        content_history=content_history,
        job_id=job.id,
        session_factory=session_factory,
    )
    return {
        "audit_id": str(audit.id),
        "status": audit.status,
        "overall_score": audit.overall_score,
    }


@register_progress_calculator("audit")
async def audit_job_progress(job: Job, db: AsyncSession) -> int:
    """Finer-grained than the generic leased-job fallback: how many of the
    five categories have reported back yet, once the orchestrator's Audit
    row exists."""
    audit_id = (
        await db.execute(select(Audit.id).where(Audit.job_id == job.id))
    ).scalar_one_or_none()
    if audit_id is None:
        return _BASE_PERCENT
    completed = (
        await db.execute(
            select(func.count())
            .select_from(AuditCategoryResult)
            .where(AuditCategoryResult.audit_id == audit_id)
        )
    ).scalar_one()
    return min(99, _BASE_PERCENT + completed * _PER_CATEGORY_PERCENT)
