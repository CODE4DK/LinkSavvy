"""In-app notifications and the per-type/per-channel preferences that
gate them. `type` is deliberately a free-form string, not a DB enum --
FRD 21's set (`subscription.*`, `audit.completed`,
`growth.weekly_report`, `content.reminder`, `product.update`,
`billing.payment_failed`) is exactly what app/notifications/service.py
and app/billing/service.py emit today, but a DB enum would mean a
migration every time a future phase adds one more type.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

NotificationChannel = Enum("in_app", "email", name="notification_channel")


class Notification(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        # Serves the notification centre's own feed query: unread-first,
        # newest-first, for one user.
        Index("ix_notifications_user_read_created", "user_id", "read_at", "created_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    action_route: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class NotificationPreference(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "channel", "type", name="uq_notification_preferences_user_channel_type"
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(NotificationChannel, nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
