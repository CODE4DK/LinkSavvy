"""One row per completed audit, feeding the dashboard's 90-day trend
sparkline. Per-category scores are nullable since a skipped or failed
category contributes no score for that run."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class ScoreHistory(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "score_history"
    __table_args__ = (
        Index("ix_score_history_user_recorded", "user_id", "recorded_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False)
    overall: Mapped[int] = mapped_column(Integer, nullable=False)
    profile: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    career: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visibility: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
