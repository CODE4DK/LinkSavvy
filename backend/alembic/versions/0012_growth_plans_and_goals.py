"""growth plans and goals

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-11 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "growth_goals",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("goal_type", sa.String(length=100), nullable=False),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        # No server_default: MySQL rejects a literal DEFAULT on TEXT/BLOB/
        # JSON columns. The ORM's own default="" (app/models/growth_goal.py)
        # is what actually supplies the value on every insert, matching
        # every other NOT NULL Text column elsewhere in this codebase
        # (none of which carry a server_default, for the same reason).
        sa.Column("target_description", sa.Text(), nullable=False),
        sa.Column("horizon_weeks", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "abandoned", name="growth_goal_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("baseline_scores", sa.JSON(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_growth_goals_user_status", "growth_goals", ["user_id", "status"], unique=False
    )

    op.create_table(
        "weekly_plans",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("focus", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "reflected", name="weekly_plan_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reflection", sa.JSON(), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ux_weekly_plans_user_week",
        "weekly_plans",
        ["user_id", "week_start"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("weekly_plans")
    op.drop_table("growth_goals")
