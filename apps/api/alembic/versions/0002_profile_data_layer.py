"""profile data layer

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
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
        "profile_import_blobs",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "profile_imports",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "source",
            sa.Enum("paste", "upload_pdf", "upload_docx", name="profile_import_source"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "parsing",
                "needs_review",
                "committed",
                "failed",
                name="profile_import_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("raw_input_ref", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("draft_payload", sa.JSON(), nullable=True),
        sa.Column("parse_warnings", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["raw_input_ref"], ["profile_import_blobs.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_profile_imports_user_id", "profile_imports", ["user_id"], unique=False)

    op.create_table(
        "profile_snapshots",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "linkedin_api",
                "paste",
                "upload_pdf",
                "upload_docx",
                "manual",
                "merged",
                name="profile_source",
            ),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("completeness_score", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "version", name="uq_profile_snapshots_user_version"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_profile_snapshots_user_id", "profile_snapshots", ["user_id"], unique=False)

    op.create_table(
        "linkedin_connections",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("oauth_identity_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("scopes", sa.String(length=512), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "sync_status",
            sa.Enum("never_synced", "syncing", "ok", "error", name="linkedin_sync_status"),
            nullable=False,
            server_default="never_synced",
        ),
        sa.Column("api_fields_available", sa.JSON(), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["oauth_identity_id"], ["oauth_identities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("oauth_identity_id", name="uq_linkedin_connections_oauth_identity"),
        **_TABLE_KWARGS,
    )


def downgrade() -> None:
    op.drop_table("linkedin_connections")
    op.drop_index("ix_profile_snapshots_user_id", table_name="profile_snapshots")
    op.drop_table("profile_snapshots")
    op.drop_index("ix_profile_imports_user_id", table_name="profile_imports")
    op.drop_table("profile_imports")
    op.drop_table("profile_import_blobs")
