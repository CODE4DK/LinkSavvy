"""assistant conversations

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-08 00:00:00.000000

The spec for this phase called this "migration 0011" -- 0001-0015 were
already in use by the time Phase 09 started (the same renumbering-in-place
disclosure every phase since Phase 08 has made). `conversations`/`messages`
are the one shared store the AI Assistant, the dashboard prompt bar, and
the absorbed Growth Coach all write into (see docs/adr/0010), which is
also why this migration drops `coach_sessions`/`coach_messages`: Phase 08's
Growth Coach now persists into these same two tables (`mode='coach'`)
instead of its own pair. `growth_goals.coach_state` is untouched -- it's
still a goal's own working-plan state, unrelated to message storage.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "mode",
            sa.Enum("auto", "tool", "coach", name="conversation_mode"),
            nullable=False,
            server_default="auto",
        ),
        sa.Column("context_snapshot", sa.JSON(), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_archived", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("asset_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_conversations_user_updated",
        "conversations",
        ["user_id", "updated_at"],
        unique=False,
    )

    op.create_table(
        "messages",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("conversation_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", "system", "tool", name="message_role"),
            nullable=False,
        ),
        sa.Column("content", sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"), nullable=False),
        sa.Column("tool_call", sa.JSON(), nullable=True),
        sa.Column("tool_run_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("ai_invocation_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("parent_message_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_run_id"], ["tool_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ai_invocation_id"], ["ai_invocations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
        unique=False,
    )

    op.drop_index("ix_coach_messages_session_created", table_name="coach_messages")
    op.drop_table("coach_messages")
    op.drop_index("ix_coach_sessions_user_status", table_name="coach_sessions")
    op.drop_table("coach_sessions")


def downgrade() -> None:
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
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

    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_user_updated", table_name="conversations")
    op.drop_table("conversations")
