from __future__ import annotations

from datetime import datetime

from sqlalchemy import Computed, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

UserRole = Enum("user", "admin", name="user_role")
UserPlan = Enum("free", "pro", name="user_plan")
UserStatus = Enum("active", "suspended", "deleted", name="user_status")


class User(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    # Generated, always-lowercase column carrying the unique constraint —
    # our citext-equivalent, since MySQL has no native case-insensitive text type.
    email_normalized: Mapped[str] = mapped_column(
        String(320),
        Computed("LOWER(email)", persisted=True),
        unique=True,
        nullable=False,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    role: Mapped[str] = mapped_column(UserRole, nullable=False, default="user")
    plan: Mapped[str] = mapped_column(UserPlan, nullable=False, default="free")
    status: Mapped[str] = mapped_column(UserStatus, nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    # ISO 3166-1 alpha-2, set at signup (billing address / declared
    # country) and never changed by a later edit -- app/billing/providers
    # /registry.py reads it once, at first-checkout time, to route the
    # subscription to Stripe or Razorpay; changing it after a subscription
    # exists would orphan the provider-side record, so the UI does not
    # expose an edit path for it once billing has started.
    billing_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
