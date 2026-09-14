"""A queue of content the output policy blocked or a user reported --
what the admin panel's Moderation view reviews and actions. `target_type`
+ `target_id` point at whatever produced the content (a Message, an
Asset, ...) without a hard FK, since the target's own table varies and
the flag must survive even if the underlying row is later deleted.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

ModerationFlagSource = Enum("ai_policy", "user_report", name="moderation_flag_source")
ModerationFlagStatus = Enum("pending", "approved", "removed", name="moderation_flag_status")


class ModerationFlag(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "moderation_flags"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(ModerationFlagSource, nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(ModerationFlagStatus, nullable=False, default="pending")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
