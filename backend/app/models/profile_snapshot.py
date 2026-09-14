from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.profiles.schema import ProfileSource

ProfileSourceColumn = Enum(*[member.value for member in ProfileSource], name="profile_source")


class ProfileSnapshotRow(PrimaryKeyMixin, TimestampMixin, Base):
    """A single committed, versioned capture of a user's profile data.

    `payload` is the canonical ProfileSnapshot (see app/profiles/schema.py),
    already validated before it ever reaches this table — see
    app/profiles/service.py's commit_snapshot, the one function that writes
    here.
    """

    __tablename__ = "profile_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_profile_snapshots_user_version"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(ProfileSourceColumn, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    completeness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
