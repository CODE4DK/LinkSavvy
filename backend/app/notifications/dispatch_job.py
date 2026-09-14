"""The `notifications.dispatch` job: the one place a notification
actually gets created and, if the user's preferences allow it, emailed.
Every notification-producing feature (billing events, audit completion,
content reminders, ...) enqueues this job rather than writing to
`notifications` directly, so retries/backoff/dead-lettering (the ordinary
job runner machinery) apply uniformly instead of each caller reinventing
its own.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.jobs.registry import register_handler
from app.models.email_log import EmailLog
from app.models.job import Job
from app.models.user import User
from app.notifications import service
from app.notifications.email.base import EmailSendError, OutboundEmail
from app.notifications.email.registry import get_email_sender
from app.notifications.templates import render_notification_email
from app.notifications.unsubscribe import unsubscribe_url
from app.settings import settings

DISPATCH_JOB_TYPE = "notifications.dispatch"


@register_handler(DISPATCH_JOB_TYPE)
async def dispatch_notification(
    job: Job, db: AsyncSession, session_factory: SessionFactory
) -> dict[str, Any] | None:
    user = await db.get(User, job.user_id)
    if user is None or user.deleted_at is not None:
        return {"skipped": "user no longer exists"}

    payload = job.payload
    notification_type = payload["type"]
    title = payload["title"]
    body = payload["body"]
    action_route = payload.get("action_route")
    metadata = payload.get("metadata") or {}

    notification = await service.create_notification(
        db,
        user_id=user.id,
        notification_type=notification_type,
        title=title,
        body=body,
        action_route=action_route,
        metadata=metadata,
    )

    email_sent = False
    if await service.channel_enabled(
        db, user_id=user.id, channel="email", notification_type=notification_type
    ):
        email_sent = await _send_email(
            db,
            user=user,
            notification_type=notification_type,
            title=title,
            body=body,
            action_route=action_route,
        )

    return {
        "in_app_created": notification is not None,
        "email_sent": email_sent,
    }


async def _send_email(
    db: AsyncSession,
    *,
    user: User,
    notification_type: str,
    title: str,
    body: str,
    action_route: str | None,
) -> bool:
    rendered = render_notification_email(
        title=title,
        body=body,
        action_label="Open LinkSavvy" if action_route else None,
        action_url=_frontend_link(action_route) if action_route else None,
        unsubscribe_url=unsubscribe_url(user_id=user.id, notification_type=notification_type),
    )
    log = EmailLog(user_id=user.id, template=notification_type, status="queued")
    db.add(log)
    await db.flush()

    sender = get_email_sender()
    try:
        message_id = await sender.send(
            OutboundEmail(
                to=user.email,
                subject=rendered.subject,
                html_body=rendered.html_body,
                text_body=rendered.text_body,
                unsubscribe_url=unsubscribe_url(
                    user_id=user.id, notification_type=notification_type
                ),
            )
        )
    except EmailSendError as exc:
        log.status = "failed"
        log.error = str(exc)
        await db.commit()
        # Re-raised so the job runner's own retry/backoff applies -- a
        # transient provider outage should retry the send, not silently
        # drop the notification's email leg.
        raise

    log.status = "sent"
    log.provider_message_id = message_id
    log.sent_at = datetime.now(UTC)
    await db.commit()
    return True


def _frontend_link(action_route: str) -> str:
    return f"{settings.frontend_url}{action_route}"
