"""dedupe and unique-constrain subscriptions.user_id

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-14 00:00:00.000000

app/billing/service.py's get_or_create_subscription is a select-then-insert
with no constraint backing it -- unlike the identical shape in
process_webhook_event (0017), which is guarded by webhook_events' own
unique constraint on (provider, provider_event_id) with an IntegrityError
fallback. Two concurrent first calls for the same user (e.g. two tabs
both loading /billing/manage right after signup) each see no existing row
and each insert one; every later `scalar_one_or_none()` keyed by user_id
then raises MultipleResultsFound, a real 500 this phase's E2E pass hit on
a real account. Existing duplicates are reconciled here (any payments on
a loser row are reassigned to the survivor, oldest row by id -- these are
UUIDv7, so time-ordered -- before the losers are deleted) so the unique
constraint this should have had from the start can actually be added.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    duplicate_user_ids = conn.execute(
        sa.text("SELECT user_id FROM subscriptions GROUP BY user_id HAVING COUNT(*) > 1")
    ).fetchall()
    for (user_id,) in duplicate_user_ids:
        rows = conn.execute(
            sa.text("SELECT id FROM subscriptions WHERE user_id = :user_id ORDER BY id"),
            {"user_id": user_id},
        ).fetchall()
        survivor_id = rows[0][0]
        for (loser_id,) in rows[1:]:
            conn.execute(
                sa.text(
                    "UPDATE payments SET subscription_id = :survivor_id "
                    "WHERE subscription_id = :loser_id"
                ),
                {"survivor_id": survivor_id, "loser_id": loser_id},
            )
            conn.execute(
                sa.text("DELETE FROM subscriptions WHERE id = :loser_id"),
                {"loser_id": loser_id},
            )

    op.create_unique_constraint("uq_subscriptions_user_id", "subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_subscriptions_user_id", "subscriptions", type_="unique")
