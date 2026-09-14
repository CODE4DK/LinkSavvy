"""The content calendar's reminder: enqueued through Phase 4's job
runner (see calendar_service.set_reminder). Phase 10 routed this through
the shared `notifications.dispatch` job (app/notifications/dispatch_job.py)
instead of calling app.services.email directly, so a "content.reminder"
notification respects the same per-user preferences (in-app/email toggle)
and gets logged to email_log like every other notification type.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.jobs.queue import enqueue
from app.jobs.registry import register_handler
from app.models.content_plan import ContentPlan
from app.models.job import Job
from app.models.user import User
from app.notifications.dispatch_job import DISPATCH_JOB_TYPE

CONTENT_REMINDER_JOB_TYPE = "content_reminder"


@register_handler(CONTENT_REMINDER_JOB_TYPE)
async def send_content_reminder(
    job: Job, db: AsyncSession, session_factory: SessionFactory
) -> dict[str, Any] | None:
    plan_id = job.payload.get("content_plan_id")
    plan = await db.get(ContentPlan, plan_id)
    if plan is None or plan.deleted_at is not None:
        return {"skipped": "content plan no longer exists"}

    user = await db.get(User, job.user_id)
    if user is None:
        return {"skipped": "user no longer exists"}

    body_text = plan.body_preview or "(no draft text saved yet -- open the calendar to add one)"
    await enqueue(
        db,
        job_type=DISPATCH_JOB_TYPE,
        payload={
            "type": "content.reminder",
            "title": "Your post is ready",
            "body": (
                "Copy it and post it yourself on LinkedIn -- LinkSavvy never posts for "
                f"you.\n\n{body_text}"
            ),
            "action_route": "/content/calendar",
        },
        user_id=user.id,
    )
    return {"dispatched_to": user.email}
