"""The `notifications.weekly_digest` job: composes the week's content
(see weekly_digest.py) and hands it to the ordinary `notifications.dispatch`
job rather than creating the notification/sending email itself -- one
place applies preferences, writes email_log, and gets retried on failure,
regardless of which feature produced the notification.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.jobs.queue import enqueue
from app.jobs.registry import register_handler
from app.models.job import Job
from app.models.user import User
from app.notifications.dispatch_job import DISPATCH_JOB_TYPE
from app.notifications.weekly_digest import compose_weekly_digest, render_digest_body

WEEKLY_DIGEST_JOB_TYPE = "notifications.weekly_digest"


@register_handler(WEEKLY_DIGEST_JOB_TYPE)
async def generate_weekly_digest(
    job: Job, db: AsyncSession, session_factory: SessionFactory
) -> dict[str, Any] | None:
    user = await db.get(User, job.user_id)
    if user is None or user.deleted_at is not None:
        return {"skipped": "user no longer exists"}

    content = await compose_weekly_digest(db, user=user)
    if not content.has_content:
        return {"skipped": "no growth activity to report"}

    await enqueue(
        db,
        job_type=DISPATCH_JOB_TYPE,
        payload={
            "type": "growth.weekly_report",
            "title": "Your weekly LinkSavvy report",
            "body": render_digest_body(content),
            "action_route": "/growth",
        },
        user_id=user.id,
    )
    return {"dispatched": True}
