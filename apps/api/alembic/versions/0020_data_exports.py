"""data exports

Revision ID: 0020
Revises: 0019
Create Date: 2026-12-15 00:00:00.000000

The one net-new table Phase 10's Section 4 (privacy) needs -- everything
else (soft/hard delete, rate limiting, security headers) is code and
policy, not schema.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "data_exports",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("encrypted_zip", sa.LargeBinary(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_data_exports_user_created", "data_exports", ["user_id", "created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_data_exports_user_created", table_name="data_exports")
    op.drop_table("data_exports")
