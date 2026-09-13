"""growth coach

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-18 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: str | None = "0012"
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
    op.add_column("growth_goals", sa.Column("coach_state", sa.JSON(), nullable=True))

    op.create_table(
        "coach_sessions",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("goal_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="coach_session_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["goal_id"], ["growth_goals.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_coach_sessions_user_status", "coach_sessions", ["user_id", "status"], unique=False
    )

    op.create_table(
        "coach_messages",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("session_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("role", sa.Enum("user", "assistant", name="coach_message_role"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["session_id"], ["coach_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_coach_messages_session_created",
        "coach_messages",
        ["session_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_coach_messages_session_created", table_name="coach_messages")
    op.drop_table("coach_messages")
    op.drop_index("ix_coach_sessions_user_status", table_name="coach_sessions")
    op.drop_table("coach_sessions")
    op.drop_column("growth_goals", "coach_state")
