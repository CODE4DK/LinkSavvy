"""growth score snapshots

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-25 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "growth_score_snapshots",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "score_type",
            sa.Enum(
                "health",
                "visibility",
                "consistency",
                "personal_branding",
                name="growth_score_snapshot_type",
            ),
            nullable=False,
        ),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ux_growth_score_snapshots_user_type_date",
        "growth_score_snapshots",
        ["user_id", "score_type", "snapshot_date"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_growth_score_snapshots_user_type_date", table_name="growth_score_snapshots")
    op.drop_table("growth_score_snapshots")
