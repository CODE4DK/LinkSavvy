from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class FeatureFlag(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feature_flags"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    enabled_globally: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rollout_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserFeatureFlag(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_feature_flags"
    __table_args__ = (
        UniqueConstraint("user_id", "flag_id", name="uq_user_feature_flag"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("feature_flags.id", ondelete="CASCADE"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
