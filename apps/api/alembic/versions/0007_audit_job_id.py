"""audit job_id

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-17 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audits", sa.Column("job_id", app.db_types.UUIDBinary(length=16), nullable=True)
    )
    op.create_foreign_key(
        "fk_audits_job_id_jobs", "audits", "jobs", ["job_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_audits_job_id", "audits", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audits_job_id", table_name="audits")
    op.drop_constraint("fk_audits_job_id_jobs", "audits", type_="foreignkey")
    op.drop_column("audits", "job_id")
