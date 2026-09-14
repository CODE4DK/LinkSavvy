"""Turns a subscription's plan into what the rest of the app actually
enforces: `User.plan` (which `plan_limits` row set applies -- see
app/billing/quota.py) and, on a downgrade, which saved assets go
read-only.

Never deletes anything. A downgrade shrinks what you can *do* going
forward; it never touches what you already made.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.user import User

# How many saved assets a free-plan user may keep *writable* at once.
# Deliberately the same number as the "saved_assets" plan_limits row's
# monthly creation-rate cap (app/billing/plan_limits_seed.py) -- one
# number for "how much workspace free gives you" rather than two that
# could drift apart.
FREE_ASSET_STORAGE_CAP = 20


async def apply_entitlements(db: AsyncSession, *, user: User, plan: str) -> None:
    """The single place a subscription event turns into account state.
    Idempotent: calling it again with the same plan is a no-op past the
    first `UPDATE`, which matters because webhook processing must be safe
    to retry (see app/billing/service.py::process_webhook_event)."""
    previous_plan = user.plan
    user.plan = plan
    await db.flush()

    if plan == "free" and previous_plan != "free":
        await _freeze_overflow_assets(db, user_id=user.id)
    elif plan == "pro":
        await _unfreeze_assets(db, user_id=user.id)


async def _freeze_overflow_assets(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    # UUIDv7 primary keys sort chronologically, so ordering by id is
    # equivalent to ordering by created_at without a second index lookup
    # (the same trick ADR 0009 and ADR 0010 both lean on elsewhere).
    ids = (
        (
            await db.execute(
                select(Asset.id)
                .where(Asset.user_id == user_id, Asset.deleted_at.is_(None))
                .order_by(Asset.id.desc())
            )
        )
        .scalars()
        .all()
    )

    keep_writable = set(ids[:FREE_ASSET_STORAGE_CAP])
    overflow = [asset_id for asset_id in ids if asset_id not in keep_writable]
    if overflow:
        await db.execute(update(Asset).where(Asset.id.in_(overflow)).values(read_only=True))


async def _unfreeze_assets(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    await db.execute(
        update(Asset)
        .where(Asset.user_id == user_id, Asset.read_only.is_(True))
        .values(read_only=False)
    )
