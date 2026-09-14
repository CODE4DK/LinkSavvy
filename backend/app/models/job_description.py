"""A saved job description a user matches resumes against -- pasted,
typed in from a URL manually (CLAUDE.md forbids scraping a live URL),
or extracted from an uploaded file.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.career.schema import JobDescriptionSource
from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

JobDescriptionSourceColumn = Enum(
    *[m.value for m in JobDescriptionSource], name="job_description_source"
)


class JobDescription(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "job_descriptions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(JobDescriptionSourceColumn, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
