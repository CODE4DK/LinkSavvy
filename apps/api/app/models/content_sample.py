"""One of the user's own past LinkedIn posts, supplied so the voice
profile has real writing to learn from. `engagement` is optional,
user-reported numbers (likes/comments/etc.) -- never scraped; see
CLAUDE.md's hard compliance rule.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

ContentSampleSource = Enum("paste", "upload_pdf", "upload_docx", name="content_sample_source")


class ContentSample(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "content_samples"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    engagement: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(ContentSampleSource, nullable=False)
