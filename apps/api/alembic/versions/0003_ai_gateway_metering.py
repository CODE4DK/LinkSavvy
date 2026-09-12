"""ai gateway metering

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-13 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from uuid6 import uuid7

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")

# Kept as a private, frozen-in-time copy rather than importing
# app.billing.plan_limits_seed — migrations must not depend on application
# code that's free to change after this migration has already shipped
# (see migration 0001's own inline copy of the default feature-flag keys
# for the same reason).
_DEFAULT_PLAN_LIMITS: list[dict[str, object]] = [
    {
        "plan": "free",
        "metric": "ai_runs",
        "limit_value": 20,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "ai_runs",
        "limit_value": 500,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "audits",
        "limit_value": 3,
        "window": "month",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "audits",
        "limit_value": 60,
        "window": "month",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "tool_runs",
        "limit_value": 15,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "tool_runs",
        "limit_value": 300,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "assistant_messages",
        "limit_value": 30,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "assistant_messages",
        "limit_value": 1000,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "saved_assets",
        "limit_value": 20,
        "window": "month",
        "overage_behaviour": "soft_warn",
    },
    {
        "plan": "pro",
        "metric": "saved_assets",
        "limit_value": 500,
        "window": "month",
        "overage_behaviour": "soft_warn",
    },
    {
        "plan": "free",
        "metric": "resume_analyses",
        "limit_value": 2,
        "window": "month",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "resume_analyses",
        "limit_value": 50,
        "window": "month",
        "overage_behaviour": "block",
    },
]


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
    ]


def _seed_plan_limits() -> None:
    plan_limits = sa.table(
        "plan_limits",
        sa.column("id", app.db_types.UUIDBinary(length=16)),
        sa.column("plan", sa.String),
        sa.column("metric", sa.String),
        sa.column("limit_value", sa.Integer),
        sa.column("window", sa.String),
        sa.column("overage_behaviour", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        plan_limits,
        [
            {"id": uuid7(), "created_at": now, "updated_at": now, **row}
            for row in _DEFAULT_PLAN_LIMITS
        ],
    )


def upgrade() -> None:
    op.create_table(
        "ai_invocations",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("prompt_id", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("tier", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "outcome",
            sa.Enum(
                "ok",
                "invalid_output",
                "provider_error",
                "quota_denied",
                "policy_blocked",
                name="ai_invocation_outcome",
            ),
            nullable=False,
        ),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_ai_invocations_user_created", "ai_invocations", ["user_id", "created_at"], unique=False
    )

    op.create_table(
        "usage_counters",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("limit_snapshot", sa.Integer(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "period_start", "metric", name="uq_usage_counters_user_period_metric"
        ),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "plan_limits",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("plan", sa.Enum("free", "pro", name="plan_limit_plan"), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=False),
        sa.Column("window", sa.Enum("day", "month", name="plan_limit_window"), nullable=False),
        sa.Column(
            "overage_behaviour",
            sa.Enum("block", "soft_warn", name="plan_limit_overage_behaviour"),
            nullable=False,
        ),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan", "metric", name="uq_plan_limits_plan_metric"),
        **_TABLE_KWARGS,
    )
    _seed_plan_limits()

    op.create_table(
        "ai_cache",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("cache_key", sa.String(length=64), nullable=False),
        sa.Column("prompt_id", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key", name="uq_ai_cache_cache_key"),
        **_TABLE_KWARGS,
    )


def downgrade() -> None:
    op.drop_table("ai_cache")
    op.drop_table("plan_limits")
    op.drop_table("usage_counters")
    op.drop_index("ix_ai_invocations_user_created", table_name="ai_invocations")
    op.drop_table("ai_invocations")
