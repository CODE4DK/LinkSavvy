"""resume pipeline

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-04 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
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
        "resumes",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "source",
            sa.Enum("upload", "built", "imported_from_profile", name="resume_source"),
            nullable=False,
        ),
        sa.Column("original_file_ref", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column("parsed", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ats_score", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["original_file_ref"], ["profile_import_blobs.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_resumes_user_active", "resumes", ["user_id", "is_active"], unique=False)

    op.create_table(
        "job_descriptions",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column(
            "source",
            sa.Enum("paste", "url_manual", "upload", name="job_description_source"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed", sa.JSON(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_job_descriptions_user", "job_descriptions", ["user_id"], unique=False)

    op.create_table(
        "resume_matches",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("resume_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("job_description_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("overall_match", sa.Integer(), nullable=False),
        sa.Column("component_scores", sa.JSON(), nullable=False),
        sa.Column("matched", sa.JSON(), nullable=False),
        sa.Column("missing", sa.JSON(), nullable=False),
        sa.Column("transferable", sa.JSON(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["job_description_id"], ["job_descriptions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_resume_matches_resume_jd",
        "resume_matches",
        ["resume_id", "job_description_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resume_matches_resume_jd", table_name="resume_matches")
    op.drop_table("resume_matches")
    op.drop_index("ix_job_descriptions_user", table_name="job_descriptions")
    op.drop_table("job_descriptions")
    op.drop_index("ix_resumes_user_active", table_name="resumes")
    op.drop_table("resumes")
