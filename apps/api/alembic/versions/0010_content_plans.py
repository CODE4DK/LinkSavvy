"""content plans

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-27 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "content_plans",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("asset_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("body_preview", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False, server_default="post"),
        sa.Column(
            "status",
            sa.Enum(
                "idea",
                "drafted",
                "ready",
                "scheduled",
                "posted",
                "skipped",
                name="content_plan_status",
            ),
            nullable=False,
            server_default="idea",
        ),
        sa.Column("planned_for", sa.Date(), nullable=False),
        sa.Column("planned_time", sa.Time(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_rule", sa.String(length=255), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("performance", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_content_plans_user_planned_for",
        "content_plans",
        ["user_id", "planned_for"],
        unique=False,
    )
    op.create_index("ix_content_plans_reminder_at", "content_plans", ["reminder_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_content_plans_reminder_at", table_name="content_plans")
    op.drop_index("ix_content_plans_user_planned_for", table_name="content_plans")
    op.drop_table("content_plans")
