from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime
from app.models.base import Base, PrimaryKeyMixin


class LoginAttempt(PrimaryKeyMixin, Base):
    """Backs IP/email rate limiting for login and registration.

    MySQL is the sole datastore (see CLAUDE.md — no Redis), so attempts
    are recorded here and pruned by age rather than kept in memory, which
    keeps the limiter correct across worker restarts and multiple processes.
    """

    __tablename__ = "login_attempts"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    email_normalized: Mapped[str | None] = mapped_column(String(320), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempted_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
