"""One payment attempt (success or failure) against a subscription --
the ledger the manage-subscription page's invoice list reads from, and
what `subscription.payment_failed` dunning emails key off."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

PaymentStatus = Enum("succeeded", "failed", "refunded", name="payment_status")


class Payment(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="usd")
    status: Mapped[str] = mapped_column(PaymentStatus, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    invoice_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
