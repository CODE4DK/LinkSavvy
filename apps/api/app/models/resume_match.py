"""A scored match between one resume and one job description --
persisted (rather than recomputed on every view) so `career.resume_jd_match`
tool runs and the Career Hub's own "match" action can share the same
record, and so a match's arithmetic can be inspected after the fact.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class ResumeMatch(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "resume_matches"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    overall_match: Mapped[int] = mapped_column(Integer, nullable=False)
    component_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    matched: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    missing: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    transferable: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
