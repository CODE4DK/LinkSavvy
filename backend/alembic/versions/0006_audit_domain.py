"""audit domain

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-15 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

import app.db_types
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
_NOW = sa.text("CURRENT_TIMESTAMP")

_CATEGORY_VALUES = ("profile", "content", "engagement", "career", "visibility")


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("profile_snapshot_id", app.db_types.UUIDBinary(length=16), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "completed_with_errors",
                "failed",
                name="audit_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "trigger",
            sa.Enum("onboarding", "manual", "scheduled", name="audit_trigger"),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["profile_snapshot_id"], ["profile_snapshots.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_audits_user_created", "audits", ["user_id", "created_at"], unique=False)

    op.create_table(
        "audit_category_results",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("audit_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "category",
            sa.Enum(*_CATEGORY_VALUES, name="audit_category_result_category"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ok", "partial", "skipped", "failed", name="audit_category_result_status"),
            nullable=False,
        ),
        sa.Column("inputs_available", sa.JSON(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "audit_id", "category", name="uq_audit_category_results_audit_category"
        ),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "audit_findings",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("audit_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "category", sa.Enum(*_CATEGORY_VALUES, name="audit_finding_category"), nullable=False
        ),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("critical", "important", "opportunity", name="audit_finding_severity"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("deterministic", sa.Boolean(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_audit_findings_audit_category", "audit_findings", ["audit_id", "category"], unique=False
    )

    op.create_table(
        "recommendations",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("audit_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column(
            "category", sa.Enum(*_CATEGORY_VALUES, name="recommendation_category"), nullable=False
        ),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("action_label", sa.String(length=128), nullable=False),
        sa.Column("action_route", sa.String(length=255), nullable=False),
        sa.Column("action_tool_id", sa.String(length=64), nullable=True),
        sa.Column("estimated_impact_points", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "done", "dismissed", name="recommendation_status"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_recommendations_user_status", "recommendations", ["user_id", "status"], unique=False
    )

    op.create_table(
        "score_history",
        sa.Column("id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("user_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("audit_id", app.db_types.UUIDBinary(length=16), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("overall", sa.Integer(), nullable=False),
        sa.Column("profile", sa.Integer(), nullable=True),
        sa.Column("content", sa.Integer(), nullable=True),
        sa.Column("engagement", sa.Integer(), nullable=True),
        sa.Column("career", sa.Integer(), nullable=True),
        sa.Column("visibility", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        **_TABLE_KWARGS,
    )
    op.create_index(
        "ix_score_history_user_recorded", "score_history", ["user_id", "recorded_at"], unique=False
    )


def downgrade() -> None:
    op.drop_table("score_history")
    op.drop_table("recommendations")
    op.drop_table("audit_findings")
    op.drop_table("audit_category_results")
    op.drop_table("audits")
