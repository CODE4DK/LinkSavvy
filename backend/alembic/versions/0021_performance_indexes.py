"""performance indexes

Revision ID: 0021
Revises: 0020
Create Date: 2026-12-19 00:00:00.000000

Phase 10 Section 5's index review: composite indexes for query patterns
that were relying on nothing but a table scan or a single-column FK
index. See docs/performance.md "Index review" for how each was found.

This list is shorter than the review's first pass: verifying every one
of these against a real MySQL instance (not just the SQLite the test
suite runs against, which doesn't enforce enough to catch this) surfaced
that `ix_subscriptions_provider_sub_id` (0017), `ix_resumes_user_active`
(0011), `ix_content_plans_user_planned_for` (0010), and
`ix_growth_goals_user_status` / the unique `ux_weekly_plans_user_week`
(both 0012) already existed under these names — the review's own query
analysis had independently rediscovered indexes earlier phases already
added, not found new gaps. Those are documented as already-satisfied in
docs/performance.md and the corresponding `app/models/*.py` Index()
declarations (added this phase for the ones that had none before, e.g.
resumes/content_plans/growth_goals), rather than re-created here.
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
    ("ix_resumes_user_created", "resumes", ["user_id", "created_at"]),
    ("ix_resume_matches_user_created", "resume_matches", ["user_id", "created_at"]),
    ("ix_content_plans_user_status", "content_plans", ["user_id", "status"]),
]


def upgrade() -> None:
    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns, unique=False)


def downgrade() -> None:
    # resume_matches.user_id has a foreign key to users.id, and
    # ix_resume_matches_user_created is the only index that covers it as
    # a leftmost column -- MySQL refuses to DROP INDEX on the sole index
    # backing a foreign key. A throwaway single-column index keeps the FK
    # covered through the drop; it's harmless to leave in place, since
    # the whole table is dropped later anyway when 0011 downgrades.
    op.create_index("ix_resume_matches_user_id_tmp", "resume_matches", ["user_id"], unique=False)
    for name, table, _columns in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
