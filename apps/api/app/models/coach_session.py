"""One user's ongoing conversation with the AI Growth Coach.
`goal_id` is nullable and SET NULL on delete -- a coaching conversation
can start before any goal exists (the interview is what produces one)
and shouldn't disappear if the goal is later abandoned.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

CoachSessionStatus = Enum("active", "archived", name="coach_session_status")


class CoachSession(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coach_sessions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("growth_goals.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(CoachSessionStatus, nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
