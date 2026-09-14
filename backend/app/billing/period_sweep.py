"""Turns time passing into entitlement changes the webhook stream alone
can't: a cancelled subscription's access ends at `current_period_end`,
and a `past_due` subscription's grace period eventually runs out. Both
are calendar facts, not events a provider ever pushes to us, so -- like
app/growth/weekly_plan_scheduler.py -- this is a separate polling loop
rather than a job type, run by cron/systemd against `python -m
app.billing.period_sweep` (see docs/runbook.md).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.entitlements import apply_entitlements
from app.db import AsyncSessionLocal, SessionFactory
from app.jobs.queue import enqueue
from app.models.subscription import Subscription
from app.models.user import User
from app.settings import settings

logger = logging.getLogger("app.billing.period_sweep")

DEFAULT_POLL_INTERVAL_SECONDS = 3600.0


async def run_once(db: AsyncSession, *, now: datetime | None = None) -> int:
    """Downgrades subscriptions whose paid access has actually run out.
    Returns how many it downgraded. `now` is a test injection seam."""
    reference = now if now is not None else datetime.now(UTC)
    downgraded = 0

    # A cancel-at-period-end (or provider-confirmed cancelled) subscription
    # keeps pro access until current_period_end -- once that passes, drop
    # to free. `expired` subscriptions (trial that never converted, say)
    # follow the same rule.
    ended = (
        (
            await db.execute(
                select(Subscription).where(
                    Subscription.status.in_(("cancelled", "expired")),
                    Subscription.plan == "pro",
                    Subscription.current_period_end.is_not(None),
                    Subscription.current_period_end <= reference,
                )
            )
        )
        .scalars()
        .all()
    )
    for subscription in ended:
        user = await db.get(User, subscription.user_id)
        if user is None:
            continue
        subscription.status = "expired"
        await apply_entitlements(db, user=user, plan="free")
        downgraded += 1

    # A past_due subscription keeps full access for a grace period so a
    # transient card decline doesn't lock someone out mid-renewal, but
    # past that window it's restricted the same as any other free user.
    grace_cutoff = reference - timedelta(days=settings.past_due_grace_period_days)
    stale = (
        (
            await db.execute(
                select(Subscription).where(
                    Subscription.status == "past_due",
                    Subscription.plan == "pro",
                    Subscription.updated_at <= grace_cutoff,
                )
            )
        )
        .scalars()
        .all()
    )
    for subscription in stale:
        user = await db.get(User, subscription.user_id)
        if user is None:
            continue
        await apply_entitlements(db, user=user, plan="free")
        await enqueue(
            db,
            job_type="notifications.dispatch",
            payload={
                "type": "billing.payment_failed",
                "title": "Your pro access has been paused",
                "body": (
                    "We couldn't collect payment after several attempts, so your "
                    "account is back on the free plan. Update your payment method "
                    "any time to pick pro back up."
                ),
                "action_route": "/billing/manage",
            },
            user_id=user.id,
        )
        downgraded += 1

    await db.commit()
    return downgraded


async def run_sweeper(
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    iterations: int | None = None,
    session_factory: SessionFactory = AsyncSessionLocal,
) -> None:
    count = 0
    while iterations is None or count < iterations:
        async with session_factory() as db:
            downgraded = await run_once(db)
            if downgraded:
                logger.info("billing_period_sweep_downgraded", extra={"count": downgraded})
        count += 1
        if iterations is None or count < iterations:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_sweeper())
