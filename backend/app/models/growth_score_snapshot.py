"""One score's value on one day, for the Growth Hub's 6-month trend
chart and before/after panel. Append-only and immutable by design (no
`updated_at`): a snapshot records what a score actually was on a given
day, so it should never be edited after the fact, only superseded by a
later day's row. At most one row per (user, score_type, day) -- see the
unique index in migration 0014.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin

GrowthScoreSnapshotType = Enum(
    "health", "visibility", "consistency", "personal_branding", name="growth_score_snapshot_type"
)


class GrowthScoreSnapshot(PrimaryKeyMixin, Base):
    __tablename__ = "growth_score_snapshots"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    score_type: Mapped[str] = mapped_column(GrowthScoreSnapshotType, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), nullable=False
    )
