"""asset versions

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-01 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")
_LongText = sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql")


def upgrade() -> None:
    op.create_table(
        "asset_versions",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("asset_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", _LongText, nullable=False),
        sa.Column("body_format", sa.String(length=16), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ux_asset_versions_asset_version",
        "asset_versions",
        ["asset_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_asset_versions_asset_version", table_name="asset_versions")
    op.drop_table("asset_versions")
