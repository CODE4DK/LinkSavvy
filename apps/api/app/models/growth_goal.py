"""A user's active growth objective -- what the weekly recommendation
engine and the AI Growth Coach both anchor their output to.
`baseline_scores` freezes the four Growth Hub scores at the moment the
goal was set, so progress can always be measured against where the user
actually started rather than a moving target.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

GrowthGoalStatus = Enum("active", "completed", "abandoned", name="growth_goal_status")


class GrowthGoal(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "growth_goals"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    goal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    horizon_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    status: Mapped[str] = mapped_column(GrowthGoalStatus, nullable=False, default="active")
    baseline_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
