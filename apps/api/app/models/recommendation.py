"""A recommendation generated from an audit finding by the deterministic
mapper in app/audit/recommendations.py. Denormalizes user_id (rather than
requiring a join through `audits`) since "my open recommendations" is the
dashboard's single most common query against this table."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

RecommendationCategory = Enum(
    "profile", "content", "engagement", "career", "visibility", name="recommendation_category"
)
RecommendationStatus = Enum(
    "open", "in_progress", "done", "dismissed", name="recommendation_status"
)


class Recommendation(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendations_user_status", "user_id", "status"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(RecommendationCategory, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    why: Mapped[str] = mapped_column(Text, nullable=False)
    action_label: Mapped[str] = mapped_column(String(128), nullable=False)
    action_route: Mapped[str] = mapped_column(String(255), nullable=False)
    # No FK: ToolDefinition doesn't exist yet (a later phase's table) --
    # per CLAUDE.md, this phase doesn't depend on a module it doesn't own
    # yet. A route always resolves even when a tool id doesn't (see
    # app/audit/recommendations.py's route-resolution test).
    action_tool_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estimated_impact_points: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(RecommendationStatus, nullable=False, default="open")
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
