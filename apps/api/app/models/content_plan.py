"""A planned, drafted, or already-posted piece of content on the
content calendar. `asset_id` is nullable and carries no FK on purpose
-- a plan can exist before any draft does (an idea, or an empty
recurring placeholder waiting to be filled), and an asset can be
deleted independently of the calendar entry that pointed to it.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

ContentPlanStatus = Enum(
    "idea", "drafted", "ready", "scheduled", "posted", "skipped", name="content_plan_status"
)


class ContentPlan(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "content_plans"
    __table_args__ = (
        # The calendar view's date-range query for one user.
        Index("ix_content_plans_user_planned_for", "user_id", "planned_for"),
        # content_history's "what have I posted before" lookup.
        Index("ix_content_plans_user_status", "user_id", "status"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUIDBinary, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    body_preview: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, default="post")
    status: Mapped[str] = mapped_column(ContentPlanStatus, nullable=False, default="idea")
    planned_for: Mapped[date] = mapped_column(Date, nullable=False)
    planned_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    reminder_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    recurrence_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    performance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
