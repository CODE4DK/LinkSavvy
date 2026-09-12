"""Per-user, per-metric quota, enforced with one atomic upsert per check.

`check_and_reserve` reserves usage *before* the expensive work happens
(the gateway calls it ahead of the provider call) so two concurrent
requests can never both observe "quota available" and both proceed —
the increment and the limit check are the same database statement, not a
read-then-write pair. `release` gives back a reservation for a call that
ultimately didn't count (a provider failure, an invalid-output that
exhausted its repair attempt, a policy block) — see app/ai/gateway.py.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import Table, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from uuid6 import uuid7

from app.errors import ApiError, ErrorCode
from app.models.plan_limit import PlanLimit
from app.models.usage_counter import UsageCounter
from app.models.user import User


class PlanLimitNotConfigured(Exception):
    """A metric has no plan_limits row for the user's plan — a seed-data
    bug, not a runtime condition a caller can recover from."""


class QuotaExceeded(ApiError):
    def __init__(
        self,
        *,
        metric: str,
        used: int,
        limit: int,
        window: str,
        resets_at: datetime,
        upgrade_required: bool,
    ) -> None:
        self.metric = metric
        self.used = used
        self.limit = limit
        self.window = window
        self.resets_at = resets_at
        self.upgrade_required = upgrade_required
        super().__init__(
            ErrorCode.QUOTA_EXCEEDED,
            f"quota exceeded for {metric}: {used}/{limit} per {window}",
            details={
                "metric": metric,
                "used": used,
                "limit": limit,
                "window": window,
                "resets_at": resets_at.isoformat(),
                "upgrade_required": upgrade_required,
            },
        )


@dataclass(frozen=True, slots=True)
class Reservation:
    """What `check_and_reserve` returns on success — pass it straight to
    `release` if the work it paid for ends up not counting."""

    user_id: uuid.UUID
    metric: str
    period_start: datetime
    amount: int


def _current_period(window: str, *, now: datetime) -> tuple[datetime, datetime]:
    if window == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)
    if window == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
        return start, end
    raise ValueError(f"unknown plan_limits window: {window!r}")


async def _get_plan_limit(db: AsyncSession, *, plan: str, metric: str) -> PlanLimit:
    limit = (
        await db.execute(
            select(PlanLimit).where(PlanLimit.plan == plan, PlanLimit.metric == metric)
        )
    ).scalar_one_or_none()
    if limit is None:
        raise PlanLimitNotConfigured(f"no plan_limits row for plan={plan!r} metric={metric!r}")
    return limit


async def check_and_reserve(
    db: AsyncSession, *, user: User, metric: str, amount: int = 1
) -> Reservation:
    plan_limit = await _get_plan_limit(db, plan=user.plan, metric=metric)
    now = datetime.now(UTC)
    period_start, period_end = _current_period(plan_limit.window, now=now)

    table = cast(Table, UsageCounter.__table__)
    values: dict[str, Any] = {
        "id": uuid7(),
        "user_id": user.id,
        "period_start": period_start,
        "period_end": period_end,
        "metric": metric,
        "used": amount,
        "limit_snapshot": plan_limit.limit_value,
        "created_at": now,
        "updated_at": now,
    }

    dialect = db.get_bind().dialect.name
    stmt: Any
    if dialect == "mysql":
        mysql_stmt = mysql_insert(table).values(**values)
        # MySQL reports 0 affected rows when ON DUPLICATE KEY UPDATE writes
        # back the same value a row already had — the IF() branch that
        # skips the increment is indistinguishable, at the rowcount level,
        # from "the guard rejected the write". Both dialects therefore give
        # the same signal: rowcount 0 == denied.
        capped = func.IF(
            table.c.used + amount <= table.c.limit_snapshot, table.c.used + amount, table.c.used
        )
        stmt = mysql_stmt.on_duplicate_key_update(used=capped, updated_at=now)
    else:
        sqlite_stmt = sqlite_insert(table).values(**values)
        stmt = sqlite_stmt.on_conflict_do_update(
            index_elements=["user_id", "period_start", "metric"],
            set_={"used": table.c.used + amount, "updated_at": now},
            where=(table.c.used + amount <= table.c.limit_snapshot),
        )

    result = cast(CursorResult[Any], await db.execute(stmt))
    await db.commit()

    if result.rowcount == 0:
        current = (
            await db.execute(
                select(UsageCounter).where(
                    UsageCounter.user_id == user.id,
                    UsageCounter.period_start == period_start,
                    UsageCounter.metric == metric,
                )
            )
        ).scalar_one()
        raise QuotaExceeded(
            metric=metric,
            used=current.used,
            limit=plan_limit.limit_value,
            window=plan_limit.window,
            resets_at=period_end,
            upgrade_required=user.plan == "free",
        )

    return Reservation(user_id=user.id, metric=metric, period_start=period_start, amount=amount)


async def release(db: AsyncSession, reservation: Reservation) -> None:
    """Gives back a reservation for work that ended up not counting.
    Never releases more than was reserved — `used` is trusted not to need
    clamping because every caller reserves before it does anything that
    could fail, and releases at most that same amount."""
    await db.execute(
        update(UsageCounter)
        .where(
            UsageCounter.user_id == reservation.user_id,
            UsageCounter.period_start == reservation.period_start,
            UsageCounter.metric == reservation.metric,
        )
        .values(used=UsageCounter.used - reservation.amount)
    )
    await db.commit()
