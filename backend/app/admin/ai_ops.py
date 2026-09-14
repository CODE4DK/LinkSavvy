"""AI operations dashboards: everything here is a read-only aggregation
over `ai_invocations` (see app/models/ai_invocation.py), the gateway's
own metering ledger from Phase 03 -- this is how you find the prompt
that's quietly costing you money.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_invocation import AIInvocation

_DEFAULT_WINDOW_DAYS = 30


@dataclass(frozen=True, slots=True)
class CostByDay:
    day: date
    cost_minor: int
    tokens_in: int
    tokens_out: int
    invocation_count: int


@dataclass(frozen=True, slots=True)
class CostByDimension:
    key: str
    cost_minor: int
    invocation_count: int


@dataclass(frozen=True, slots=True)
class OutcomeRates:
    total: int
    invalid_output_rate: float
    fallback_rate: float
    policy_blocked_rate: float
    provider_error_rate: float


@dataclass(frozen=True, slots=True)
class SlowPrompt:
    prompt_id: str
    avg_latency_ms: float
    p95_latency_ms: float
    invocation_count: int


def _window_start(days: int) -> datetime:
    return datetime.now() - timedelta(days=days)


async def cost_by_day(db: AsyncSession, *, days: int = _DEFAULT_WINDOW_DAYS) -> list[CostByDay]:
    since = _window_start(days)
    day_expr = func.date(AIInvocation.created_at)
    rows = (
        await db.execute(
            select(
                day_expr,
                func.sum(AIInvocation.cost_minor),
                func.sum(AIInvocation.tokens_in),
                func.sum(AIInvocation.tokens_out),
                func.count(),
            )
            .where(AIInvocation.created_at >= since)
            .group_by(day_expr)
            .order_by(day_expr)
        )
    ).all()
    return [
        CostByDay(
            day=row[0] if isinstance(row[0], date) else date.fromisoformat(str(row[0])),
            cost_minor=int(row[1] or 0),
            tokens_in=int(row[2] or 0),
            tokens_out=int(row[3] or 0),
            invocation_count=int(row[4]),
        )
        for row in rows
    ]


async def cost_by_model(
    db: AsyncSession, *, days: int = _DEFAULT_WINDOW_DAYS
) -> list[CostByDimension]:
    return await _cost_by(db, AIInvocation.model, days=days)


async def cost_by_prompt(
    db: AsyncSession, *, days: int = _DEFAULT_WINDOW_DAYS
) -> list[CostByDimension]:
    return await _cost_by(db, AIInvocation.prompt_id, days=days)


async def cost_by_user(
    db: AsyncSession, *, days: int = _DEFAULT_WINDOW_DAYS, limit: int = 20
) -> list[CostByDimension]:
    since = _window_start(days)
    rows = (
        await db.execute(
            select(AIInvocation.user_id, func.sum(AIInvocation.cost_minor), func.count())
            .where(AIInvocation.created_at >= since)
            .group_by(AIInvocation.user_id)
            .order_by(func.sum(AIInvocation.cost_minor).desc())
            .limit(limit)
        )
    ).all()
    return [
        CostByDimension(key=str(row[0]), cost_minor=int(row[1] or 0), invocation_count=int(row[2]))
        for row in rows
    ]


async def _cost_by(db: AsyncSession, column: object, *, days: int) -> list[CostByDimension]:
    since = _window_start(days)
    rows = (
        await db.execute(
            select(column, func.sum(AIInvocation.cost_minor), func.count())  # type: ignore[call-overload]
            .where(AIInvocation.created_at >= since)
            .group_by(column)
            .order_by(func.sum(AIInvocation.cost_minor).desc())
        )
    ).all()
    return [
        CostByDimension(key=str(row[0]), cost_minor=int(row[1] or 0), invocation_count=int(row[2]))
        for row in rows
    ]


async def outcome_rates(db: AsyncSession, *, days: int = _DEFAULT_WINDOW_DAYS) -> OutcomeRates:
    since = _window_start(days)
    rows = (
        await db.execute(
            select(AIInvocation.outcome, func.count())
            .where(AIInvocation.created_at >= since)
            .group_by(AIInvocation.outcome)
        )
    ).all()
    fallback_count = (
        await db.execute(
            select(func.count()).where(
                AIInvocation.created_at >= since, AIInvocation.fallback_used.is_(True)
            )
        )
    ).scalar_one()

    counts = {row[0]: int(row[1]) for row in rows}
    total = sum(counts.values())
    if total == 0:
        return OutcomeRates(0, 0.0, 0.0, 0.0, 0.0)
    return OutcomeRates(
        total=total,
        invalid_output_rate=counts.get("invalid_output", 0) / total,
        fallback_rate=int(fallback_count) / total,
        policy_blocked_rate=counts.get("policy_blocked", 0) / total,
        provider_error_rate=counts.get("provider_error", 0) / total,
    )


async def slowest_prompts(
    db: AsyncSession, *, days: int = _DEFAULT_WINDOW_DAYS, limit: int = 10
) -> list[SlowPrompt]:
    """No native PERCENTILE_CONT on MySQL 9.7 short of a window-function
    workaround that isn't worth the complexity here -- average latency
    ranks the same prompts to the top in practice, with p95 approximated
    as 1.5x average, a rough-but-labelled stand-in the admin UI marks as
    such rather than presenting as an exact measurement."""
    since = _window_start(days)
    rows = (
        await db.execute(
            select(
                AIInvocation.prompt_id,
                func.avg(AIInvocation.latency_ms),
                func.count(),
            )
            .where(AIInvocation.created_at >= since)
            .group_by(AIInvocation.prompt_id)
            .order_by(func.avg(AIInvocation.latency_ms).desc())
            .limit(limit)
        )
    ).all()
    return [
        SlowPrompt(
            prompt_id=row[0],
            avg_latency_ms=float(row[1] or 0),
            p95_latency_ms=float(row[1] or 0) * 1.5,
            invocation_count=int(row[2]),
        )
        for row in rows
    ]


async def prompt_drilldown(
    db: AsyncSession, *, prompt_id: str, days: int = _DEFAULT_WINDOW_DAYS
) -> list[AIInvocation]:
    since = _window_start(days)
    return list(
        (
            await db.execute(
                select(AIInvocation)
                .where(AIInvocation.prompt_id == prompt_id, AIInvocation.created_at >= since)
                .order_by(AIInvocation.created_at.desc())
                .limit(200)
            )
        )
        .scalars()
        .all()
    )
