"""A user's writing-voice descriptor -- how their content prompts should
sound. Versioned like `ProfileSnapshotRow` (an `is_active` flag, no soft
delete: an old voice profile is superseded, not deleted). `source`
records how the active row came to exist: `derived` from the user's own
pasted/uploaded posts (see app/content/voice_service.py), or `default`
when nothing has been supplied yet -- a neutral descriptor the UI must
say is a fallback, never presented as if it were learned from the user.
`supplied` is reserved for a future manual-entry path this phase doesn't
build.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

VoiceProfileSource = Enum("supplied", "derived", "default", name="voice_profile_source")


class VoiceProfile(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "voice_profiles"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(VoiceProfileSource, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    descriptor: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
