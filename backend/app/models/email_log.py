"""One row per outbound email attempt -- what the admin panel's platform
health view and bounce handling both read from (see
app/notifications/email/*.py)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

EmailLogStatus = Enum("queued", "sent", "failed", "bounced", name="email_log_status")


class EmailLog(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_log"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    template: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(EmailLogStatus, nullable=False, default="queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
