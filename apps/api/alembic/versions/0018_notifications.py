"""notifications, notification preferences, and the email log

Revision ID: 0018
Revises: 0017
Create Date: 2026-12-08 00:00:00.000000

Phase 10's spec called this "migration 0013" -- 0001-0017 were already in
use by the time this phase started, the same renumbering-in-place
disclosure every phase since Phase 08 has made.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("action_route", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_notifications_user_created", "notifications", ["user_id", "created_at"], unique=False
    )
    op.create_index(
        "ix_notifications_user_unread", "notifications", ["user_id", "read_at"], unique=False
    )

    op.create_table(
        "notification_preferences",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "channel", sa.Enum("in_app", "email", name="notification_channel"), nullable=False
        ),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "channel", "type", name="uq_notification_preferences_user_channel_type"
        ),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "email_log",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("template", sa.String(length=64), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("queued", "sent", "failed", "bounced", name="email_log_status"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_email_log_user_created", "email_log", ["user_id", "created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_email_log_user_created", table_name="email_log")
    op.drop_table("email_log")
    op.drop_table("notification_preferences")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_table("notifications")
