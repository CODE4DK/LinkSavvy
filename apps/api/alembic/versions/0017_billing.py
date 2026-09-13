"""billing: subscriptions, payments, webhook events

Revision ID: 0017
Revises: 0016
Create Date: 2026-12-01 00:00:00.000000

Phase 10's spec called this "migration 0012" -- 0001-0016 were already in
use by the time this phase started, the same renumbering-in-place
disclosure every phase since Phase 08 has made.

`users.billing_country` is added here rather than in its own migration:
it exists purely to drive region routing for the tables this migration
introduces (see app/billing/providers/registry.py) and has no meaning
without them.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.add_column("users", sa.Column("billing_country", sa.String(length=2), nullable=True))
    op.add_column(
        "assets",
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "provider", sa.Enum("stripe", "razorpay", name="subscription_provider"), nullable=False
        ),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column(
            "plan",
            sa.Enum("free", "pro", name="subscription_plan"),
            nullable=False,
            server_default="free",
        ),
        sa.Column(
            "interval",
            sa.Enum("month", "year", name="subscription_interval"),
            nullable=False,
            server_default="month",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "trialing",
                "active",
                "past_due",
                "paused",
                "cancelled",
                "expired",
                name="subscription_status",
            ),
            nullable=False,
            server_default="trialing",
        ),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="usd"),
        sa.Column("amount_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_subscriptions_user_status", "subscriptions", ["user_id", "status"], unique=False
    )
    op.create_index(
        "ix_subscriptions_provider_sub_id",
        "subscriptions",
        ["provider", "provider_subscription_id"],
        unique=False,
    )

    op.create_table(
        "payments",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("subscription_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="usd"),
        sa.Column(
            "status",
            sa.Enum("succeeded", "failed", "refunded", name="payment_status"),
            nullable=False,
        ),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("invoice_url", sa.String(length=1024), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_payments_subscription_created",
        "payments",
        ["subscription_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "provider", sa.Enum("stripe", "razorpay", name="webhook_event_provider"), nullable=False
        ),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "processed", "failed", name="webhook_event_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider", "provider_event_id", name="uq_webhook_events_provider_event"
        ),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_webhook_events_status_received",
        "webhook_events",
        ["status", "received_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_events_status_received", table_name="webhook_events")
    op.drop_table("webhook_events")
    op.drop_index("ix_payments_subscription_created", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_subscriptions_provider_sub_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_status", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_column("assets", "read_only")
    op.drop_column("users", "billing_country")
