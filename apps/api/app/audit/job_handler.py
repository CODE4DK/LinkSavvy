"""Registers the `"audit"` job type against the background job runner
(app/jobs/) -- `POST /api/v1/audits` enqueues one of these rather than
running the orchestrator inline, so a slow category never blocks the
request. The API layer is expected to have already validated quota and
that the user has an active profile snapshot before enqueueing; the
errors raised here are defensive, not the normal path.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.orchestrator import run_audit
from app.db import SessionFactory
from app.jobs.registry import register_handler
from app.models.job import Job
from app.models.user import User
from app.profiles.service import get_active_snapshot


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

    audit = await run_audit(
        user=user,
        db=db,
        snapshot_row=snapshot_row,
        trigger=job.payload.get("trigger", "manual"),
        target_role=job.payload.get("target_role"),
        content_history=job.payload.get("content_history"),
        session_factory=session_factory,
    )
    return {
        "audit_id": str(audit.id),
        "status": audit.status,
        "overall_score": audit.overall_score,
    }
