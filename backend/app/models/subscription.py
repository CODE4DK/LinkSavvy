"""A user's billing relationship with one payment provider.

`provider` is chosen once at signup time by region routing (see
app/billing/providers/registry.py) and never changes for the life of a
subscription -- moving a subscriber from Stripe to Razorpay (or back)
would mean cancelling one and starting a fresh one, not mutating this row.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

SubscriptionProvider = Enum("stripe", "razorpay", name="subscription_provider")
SubscriptionPlan = Enum("free", "pro", name="subscription_plan")
SubscriptionInterval = Enum("month", "year", name="subscription_interval")
SubscriptionStatus = Enum(
    "trialing",
    "active",
    "past_due",
    "paused",
    "cancelled",
    "expired",
    name="subscription_status",
)


class Subscription(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        # app/billing/period_sweep.py's two sweeps: cancelled/expired pro
        # subscriptions past their period end, and past_due pro
        # subscriptions past their grace window.
        Index("ix_subscriptions_status_plan_period_end", "status", "plan", "current_period_end"),
        Index("ix_subscriptions_status_plan_updated", "status", "plan", "updated_at"),
        # app/billing/service.py's webhook-event-to-subscription lookup.
        Index("ix_subscriptions_provider_sub_id", "provider", "provider_subscription_id"),
        # get_or_create_subscription is a select-then-insert; this is the
        # actual guarantee against two concurrent first calls for the same
        # user each inserting their own row (the SELECT alone can't stop
        # that race -- see app/billing/service.py).
        UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(SubscriptionProvider, nullable=False)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[str] = mapped_column(SubscriptionPlan, nullable=False, default="free")
    interval: Mapped[str] = mapped_column(SubscriptionInterval, nullable=False, default="month")
    status: Mapped[str] = mapped_column(SubscriptionStatus, nullable=False, default="trialing")
    current_period_start: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="usd")
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
