from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class RefreshToken(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        # Session listing/revocation filters a user's tokens by whether
        # they're revoked.
        Index("ix_refresh_tokens_user_revoked", "user_id", "revoked_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Shared by every token descended from the same login; reused-token
    # detection revokes the whole family at once.
    family_id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(UUIDBinary, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
