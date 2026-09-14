"""A user's resume: the parsed `ResumeDocument` (see app/career/schema.py)
plus versioning and an `is_active` flag, mirroring `VoiceProfile`'s
pattern -- a new upload or edit creates a new version rather than
overwriting history, and exactly one version is active at a time.
`original_file_ref` reuses `ProfileImportBlob` (encrypted-at-rest blob
storage) rather than a new resume-specific table -- see docs/adr/0008.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.career.schema import ResumeSource
from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

ResumeSourceColumn = Enum(*[m.value for m in ResumeSource], name="resume_source")


class Resume(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "resumes"
    __table_args__ = (
        # Activation flips is_active off for a user's other resumes;
        # listing orders by created_at for one user.
        Index("ix_resumes_user_active", "user_id", "is_active"),
        Index("ix_resumes_user_created", "user_id", "created_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(ResumeSourceColumn, nullable=False)
    original_file_ref: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("profile_import_blobs.id", ondelete="SET NULL"), nullable=True
    )
    parsed: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
