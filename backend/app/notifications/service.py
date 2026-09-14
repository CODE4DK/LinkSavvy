"""In-app notifications and the preferences that gate both them and the
email side-channel. Absence of a `notification_preferences` row means
"enabled" -- a user who has never touched their preferences still gets
notified, matching the same "no row = default" pattern
app/services/feature_flags.py uses for flags.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.notification import Notification, NotificationPreference

# FRD 21's notification types. Kept here (not a DB enum -- see
# app/models/notification.py) as the source of truth the preferences
# page and the digest job both read from.
NOTIFICATION_TYPES: list[str] = [
    "subscription.activated",
    "subscription.renewed",
    "subscription.payment_failed",
    "subscription.cancelled",
    "subscription.plan_changed",
    "billing.payment_failed",
    "audit.completed",
    "growth.weekly_report",
    "content.reminder",
    "product.update",
    "privacy.export_ready",
]

# Product updates are the one type that defaults to email-off: everything
# else is operationally important to the user's own account or content;
# a product announcement is not, and inboxes fill up fast with those.
_DEFAULT_EMAIL_DISABLED_TYPES = frozenset({"product.update"})


class NotificationNotFound(ApiError):
    def __init__(self) -> None:
        super().__init__(ErrorCode.NOT_FOUND, "no such notification")


async def channel_enabled(
    db: AsyncSession, *, user_id: uuid.UUID, channel: str, notification_type: str
) -> bool:
    row = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == channel,
                NotificationPreference.type == notification_type,
            )
        )
    ).scalar_one_or_none()
    if row is not None:
        return row.enabled
    return not (channel == "email" and notification_type in _DEFAULT_EMAIL_DISABLED_TYPES)


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    body: str,
    action_route: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Notification | None:
    """Returns None (and creates nothing) if the user has turned this
    type off for in_app -- the caller (dispatch_job) still separately
    checks the email channel for whether to also send mail."""
    if not await channel_enabled(
        db, user_id=user_id, channel="in_app", notification_type=notification_type
    ):
        return None

    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        action_route=action_route,
        metadata_=metadata or {},
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


@dataclass(frozen=True, slots=True)
class NotificationPage:
    items: list[Notification]
    unread_count: int


async def list_notifications(
    db: AsyncSession, *, user_id: uuid.UUID, limit: int = 30, unread_only: bool = False
) -> NotificationPage:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    query = query.order_by(Notification.created_at.desc()).limit(limit)
    items = (await db.execute(query)).scalars().all()

    unread_count = (
        await db.execute(
            select(Notification.id).where(
                Notification.user_id == user_id, Notification.read_at.is_(None)
            )
        )
    ).all()
    return NotificationPage(items=list(items), unread_count=len(unread_count))


async def mark_read(db: AsyncSession, *, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotificationNotFound()
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await db.commit()


async def mark_all_read(db: AsyncSession, *, user_id: uuid.UUID) -> int:
    result = cast(
        CursorResult[Any],
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        ),
    )
    await db.commit()
    return result.rowcount or 0


async def list_preferences(db: AsyncSession, *, user_id: uuid.UUID) -> list[tuple[str, str, bool]]:
    """Every (channel, type) pair, materialising the default for any the
    user has never overridden -- the preferences page always shows a
    complete grid, never a partial one that looks broken."""
    rows = {
        (row.channel, row.type): row.enabled
        for row in (
            await db.execute(
                select(NotificationPreference).where(NotificationPreference.user_id == user_id)
            )
        )
        .scalars()
        .all()
    }
    result: list[tuple[str, str, bool]] = []
    for notification_type in NOTIFICATION_TYPES:
        for channel in ("in_app", "email"):
            if (channel, notification_type) in rows:
                result.append((channel, notification_type, rows[(channel, notification_type)]))
            else:
                default = (
                    channel != "email" or notification_type not in _DEFAULT_EMAIL_DISABLED_TYPES
                )
                result.append((channel, notification_type, default))
    return result


async def set_preference(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    channel: str,
    notification_type: str,
    enabled: bool,
) -> None:
    row = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == channel,
                NotificationPreference.type == notification_type,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        db.add(
            NotificationPreference(
                user_id=user_id, channel=channel, type=notification_type, enabled=enabled
            )
        )
    else:
        row.enabled = enabled
    await db.commit()
