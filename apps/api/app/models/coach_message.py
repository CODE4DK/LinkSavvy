"""One turn of a CoachSession conversation. `metadata_` carries an
assistant message's actionable tool proposal, if any -- see
app.growth.coach for the shape.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

CoachMessageRole = Enum("user", "assistant", name="coach_message_role")


class CoachMessage(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coach_messages"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("coach_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(CoachMessageRole, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
