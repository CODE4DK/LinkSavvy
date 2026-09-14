"""performance indexes

Revision ID: 0021
Revises: 0020
Create Date: 2026-12-19 00:00:00.000000

Phase 10 Section 5's index review: composite indexes for query patterns
that were relying on nothing but a table scan or a single-column FK
index. See docs/performance.md "Index review" for how each was found and
the corresponding app/models/*.py Index() declarations these mirror.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_notifications_user_read_created", "notifications", ["user_id", "read_at", "created_at"]),
    ("ix_login_attempts_email_attempted", "login_attempts", ["email_normalized", "attempted_at"]),
    ("ix_login_attempts_ip_attempted", "login_attempts", ["ip_hash", "attempted_at"]),
    ("ix_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "revoked_at"]),
    (
        "ix_subscriptions_status_plan_period_end",
        "subscriptions",
        ["status", "plan", "current_period_end"],
    ),
    ("ix_subscriptions_status_plan_updated", "subscriptions", ["status", "plan", "updated_at"]),
    (
        "ix_subscriptions_provider_sub_id",
        "subscriptions",
        ["provider", "provider_subscription_id"],
    ),
    ("ix_resumes_user_active", "resumes", ["user_id", "is_active"]),
    ("ix_resumes_user_created", "resumes", ["user_id", "created_at"]),
    ("ix_resume_matches_user_created", "resume_matches", ["user_id", "created_at"]),
    ("ix_content_plans_user_planned_for", "content_plans", ["user_id", "planned_for"]),
    ("ix_content_plans_user_status", "content_plans", ["user_id", "status"]),
    ("ix_growth_goals_user_status", "growth_goals", ["user_id", "status"]),
    ("ix_weekly_plans_user_week_start", "weekly_plans", ["user_id", "week_start"]),
]


def upgrade() -> None:
    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns, unique=False)


def downgrade() -> None:
    for name, table, _columns in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
