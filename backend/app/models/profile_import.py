from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.profiles.schema import ImportSource, ImportStatus

ImportSourceColumn = Enum(*[m.value for m in ImportSource], name="profile_import_source")
ImportStatusColumn = Enum(*[m.value for m in ImportStatus], name="profile_import_status")


class ProfileImportBlob(PrimaryKeyMixin, Base):
    """Encrypted-at-rest storage for a raw paste or uploaded file.

    Stands in for real object storage for now (see CLAUDE.md — no new
    infra without a stated need); `profile_imports.raw_input_ref` points
    at a row here by id, so swapping this out later for S3-alike storage
    only touches this model and the two functions that read/write it.
    """

    __tablename__ = "profile_import_blobs"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class ProfileImportRow(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "profile_imports"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(ImportSourceColumn, nullable=False)
    status: Mapped[str] = mapped_column(
        ImportStatusColumn, nullable=False, default=ImportStatus.PENDING.value
    )
    raw_input_ref: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("profile_import_blobs.id", ondelete="SET NULL"), nullable=True
    )
    # The parsed-but-not-yet-committed draft ProfileSnapshot, held here so
    # the review step (wizard step 3) can show it and the eventual commit
    # can pass it straight to commit_snapshot unchanged if the user makes
    # no edits.
    draft_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    parse_warnings: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
