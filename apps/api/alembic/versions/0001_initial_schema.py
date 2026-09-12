"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-12 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from uuid6 import uuid7

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
    ]


_DEFAULT_FLAG_KEYS = [
    "hub.profile",
    "hub.content",
    "hub.engagement",
    "hub.career",
    "hub.growth",
    "hub.workspace",
    "assistant",
    "audit",
]


def _seed_default_feature_flags() -> None:
    """Every hub ships dark until explicitly enabled (see CLAUDE.md)."""
    feature_flags = sa.table(
        "feature_flags",
        sa.column("id", app.db_types.UUIDBinary(length=16)),
        sa.column("key", sa.String),
        sa.column("enabled_globally", sa.Boolean),
        sa.column("rollout_percent", sa.Integer),
        sa.column("description", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        feature_flags,
        [
            {
                "id": uuid7(),
                "key": key,
                "enabled_globally": False,
                "rollout_percent": 0,
                "description": f"Auto-seeded flag for {key}",
                "created_at": now,
                "updated_at": now,
            }
            for key in _DEFAULT_FLAG_KEYS
        ],
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "email_normalized",
            sa.String(length=320),
            sa.Computed("LOWER(email)", persisted=True),
            nullable=False,
        ),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="user_role"),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "plan",
            sa.Enum("free", "pro", name="user_plan"),
            nullable=False,
            server_default="free",
        ),
        sa.Column(
            "status",
            sa.Enum("active", "suspended", "deleted", name="user_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_normalized", name="uq_users_email_normalized"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "feature_flags",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("enabled_globally", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rollout_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_feature_flags_key"),
        **_TABLE_KWARGS,
    )
    _seed_default_feature_flags()

    op.create_table(
        "oauth_identities",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("provider", sa.Enum("linkedin", name="oauth_provider"), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("scopes", sa.String(length=512), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("family_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"], unique=False)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "email_verifications",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_email_verifications_token_hash"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "password_resets",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_password_resets_token_hash"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "user_feature_flags",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("flag_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["flag_id"], ["feature_flags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "flag_id", name="uq_user_feature_flag"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "audit_log",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("actor_user_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"], unique=False)

    op.create_table(
        "login_attempts",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("email_normalized", sa.String(length=320), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("succeeded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_login_attempts_email_normalized",
        "login_attempts",
        ["email_normalized"],
        unique=False,
    )
    op.create_index("ix_login_attempts_ip_hash", "login_attempts", ["ip_hash"], unique=False)

    op.create_table(
        "oauth_login_states",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False),
        sa.Column("code_verifier", sa.String(length=128), nullable=False),
        sa.Column("nonce", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state", name="uq_oauth_login_states_state"),
        **_TABLE_KWARGS,
    )


def downgrade() -> None:
    op.drop_table("oauth_login_states")
    op.drop_index("ix_login_attempts_ip_hash", table_name="login_attempts")
    op.drop_index("ix_login_attempts_email_normalized", table_name="login_attempts")
    op.drop_table("login_attempts")
    op.drop_index("ix_audit_log_actor_user_id", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_table("user_feature_flags")
    op.drop_table("password_resets")
    op.drop_table("email_verifications")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("oauth_identities")
    op.drop_table("feature_flags")
    op.drop_table("users")
