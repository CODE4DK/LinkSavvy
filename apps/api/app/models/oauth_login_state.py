from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin


class OAuthLoginState(PrimaryKeyMixin, Base):
    """Server-side PKCE/state/nonce storage for the LinkedIn OAuth dance.

    Short-lived (a few minutes) and consumed on callback; kept in MySQL
    rather than memory so it works correctly behind multiple API workers.

    `user_id` is set only for the profile-connect flow (Phase 02): an
    already-authenticated user linking LinkedIn for data sync, where the
    browser redirect round-trip can't carry their Authorization header,
    so this is how the callback knows whose account to attach tokens to.
    It's left null for the sign-in flow (Phase 01), which has no user yet.
    """

    __tablename__ = "oauth_login_states"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    state: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    code_verifier: Mapped[str] = mapped_column(String(128), nullable=False)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
