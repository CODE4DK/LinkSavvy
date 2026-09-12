from __future__ import annotations

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime
from app.models.base import Base, PrimaryKeyMixin


class OAuthLoginState(PrimaryKeyMixin, Base):
    """Server-side PKCE/state/nonce storage for the LinkedIn OAuth dance.

    Short-lived (a few minutes) and consumed on callback; kept in MySQL
    rather than memory so it works correctly behind multiple API workers.
    """

    __tablename__ = "oauth_login_states"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    state: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    code_verifier: Mapped[str] = mapped_column(String(128), nullable=False)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
