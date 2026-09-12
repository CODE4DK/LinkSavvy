"""dev playground feature flag

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-14 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from uuid6 import uuid7

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_FLAG_KEY = "dev.playground"


def upgrade() -> None:
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
                "key": _FLAG_KEY,
                # Admin-only regardless (see app/deps.py's get_current_admin),
                # so there's no exposure risk in shipping this on by default --
                # unlike a hub flag, it isn't gating an incomplete feature.
                "enabled_globally": True,
                "rollout_percent": 0,
                "description": "Admin-only harness for running/streaming any registered AI prompt.",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM feature_flags WHERE `key` = :key").bindparams(key=_FLAG_KEY))
