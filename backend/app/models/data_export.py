"""A completed `POST /me/export` job's output -- the ZIP itself, stored
encrypted at rest (see app/security/crypto.py) since it's a full copy of
one user's data. Self-expiring: the download link stops working after
`expires_at`, and the scheduled retention sweep deletes the row."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class DataExport(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "data_exports"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    encrypted_zip: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
