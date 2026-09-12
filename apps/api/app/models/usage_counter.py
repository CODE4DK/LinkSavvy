"""Per-user, per-period, per-metric usage. One row is the atomic unit
`app/billing/quota.py` increments — see its `check_and_reserve`."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class UsageCounter(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "usage_counters"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "period_start", "metric", name="uq_usage_counters_user_period_metric"
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    period_end: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # The limit in effect when this period's counter was first created —
    # kept alongside `used` so a mid-period plan_limits change never
    # rewrites history for a period that already started under the old one.
    limit_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
