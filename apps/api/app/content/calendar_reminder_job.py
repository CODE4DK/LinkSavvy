"""The content calendar's reminder: enqueued through Phase 4's job
runner (see calendar_service.set_reminder), sent through Phase 1's
mail sender. Proper notifications infrastructure arrives in a later
phase -- this is deliberately just "enqueue a job, send an email",
reusing what already exists rather than building anything new.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.jobs.registry import register_handler
from app.models.content_plan import ContentPlan
from app.models.job import Job
from app.models.user import User
from app.services.email import send_email
from app.settings import settings

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

    calendar_link = f"{settings.frontend_url}/content/calendar"
    body_text = plan.body_preview or "(no draft text saved yet -- open the calendar to add one)"
    await send_email(
        to=user.email,
        subject="Your post is ready -- here it is",
        text_body=(
            f"Your post is ready. Copy it and post it yourself on LinkedIn -- "
            f"LinkSavvy never posts for you.\n\n{body_text}\n\n{calendar_link}"
        ),
        html_body=(
            f"<p>Your post is ready. Copy it and post it yourself on LinkedIn -- "
            f"LinkSavvy never posts for you.</p>"
            f"<pre>{body_text}</pre>"
            f'<p><a href="{calendar_link}">Open your calendar</a></p>'
        ),
    )
    return {"sent_to": user.email}
