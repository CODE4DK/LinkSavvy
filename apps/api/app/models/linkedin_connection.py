from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.profiles.schema import LinkedInSyncStatus

LinkedInSyncStatusColumn = Enum(*[m.value for m in LinkedInSyncStatus], name="linkedin_sync_status")


class LinkedInConnection(PrimaryKeyMixin, TimestampMixin, Base):
    """Tracks profile-sync state for a user's linked LinkedIn identity.

    Distinct from `oauth_identities` (Phase 01, sign-in) — this row only
    exists once a user has opted into pulling profile data, and records
    what the API actually granted us, never anything scraped or inferred.
    """

    __tablename__ = "linkedin_connections"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    oauth_identity_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary,
        ForeignKey("oauth_identities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    scopes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    sync_status: Mapped[str] = mapped_column(
        LinkedInSyncStatusColumn, nullable=False, default=LinkedInSyncStatus.NEVER_SYNCED.value
    )
    api_fields_available: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
