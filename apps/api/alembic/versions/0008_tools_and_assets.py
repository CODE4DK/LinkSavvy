"""tools and assets

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-18 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
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
        "tool_runs",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("tool_id", sa.String(length=96), nullable=False),
        sa.Column("prompt_id", sa.String(length=96), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("context_keys", sa.JSON(), nullable=False),
        sa.Column("ai_invocation_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("status", sa.Enum("succeeded", "failed", name="tool_run_status"), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("rating", sa.Enum("up", "down", name="tool_run_rating"), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("parent_run_id", app.db_types.UUIDBinary(length=16), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ai_invocation_id"], ["ai_invocations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_run_id"], ["tool_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_tool_runs_user_tool_created",
        "tool_runs",
        ["user_id", "tool_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "asset_folders",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", app.db_types.UUIDBinary(length=16), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["asset_folders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "assets",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "post",
                "headline",
                "about",
                "experience_bullets",
                "comment",
                "message",
                "resume",
                "cover_letter",
                "job_description",
                "analysis",
                "conversation",
                "template",
                "carousel",
                "roadmap",
                name="asset_type",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"), nullable=False),
        sa.Column(
            "body_format",
            sa.Enum("text", "markdown", "json", name="asset_body_format"),
            nullable=False,
            server_default="text",
        ),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("source_tool_run_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("is_favourite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("folder_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["asset_folders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_assets_user_folder", "assets", ["user_id", "folder_id"], unique=False)
    op.create_index(
        "ft_assets_title_body",
        "assets",
        ["title", "body"],
        unique=False,
        mysql_prefix="FULLTEXT",
    )


def downgrade() -> None:
    op.drop_index("ft_assets_title_body", table_name="assets")
    op.drop_index("ix_assets_user_folder", table_name="assets")
    op.drop_table("assets")
    op.drop_table("asset_folders")
    op.drop_index("ix_tool_runs_user_tool_created", table_name="tool_runs")
    op.drop_table("tool_runs")
