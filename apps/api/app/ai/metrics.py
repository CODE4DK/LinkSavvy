"""Observability metrics for the AI gateway, computed on demand from
`ai_invocations` — no separate metrics store, consistent with CLAUDE.md's
MySQL-only rule. Metrics are computed at request time over a rolling
window rather than kept as long-lived in-process counters, so they stay
correct across multiple workers and process restarts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_invocation import AIInvocation


@dataclass(frozen=True, slots=True)
class GatewayMetrics:
    window_hours: int
    total_invocations: int
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    cache_hit_rate: float | None
    fallback_rate: float | None
    invalid_output_rate: float | None
    cost_per_user_per_day_minor: dict[str, int]


def _percentile(sorted_values: list[int], fraction: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (len(sorted_values) - 1) * fraction
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    if lower == upper:
        return float(sorted_values[lower])
    lower_weight = sorted_values[lower] * (upper - rank)
    upper_weight = sorted_values[upper] * (rank - lower)
    return lower_weight + upper_weight


async def compute_metrics(db: AsyncSession, *, window_hours: int = 24) -> GatewayMetrics:
    since = datetime.now(UTC) - timedelta(hours=window_hours)
    rows = (
        await db.execute(
            select(
                AIInvocation.latency_ms,
                AIInvocation.cached,
                AIInvocation.fallback_used,
                AIInvocation.outcome,
                AIInvocation.cost_minor,
                AIInvocation.user_id,
                AIInvocation.created_at,
            ).where(AIInvocation.created_at >= since)
        )
    ).all()

    total = len(rows)
    latencies = sorted(row.latency_ms for row in rows)
    cache_hits = sum(1 for row in rows if row.cached)
    fallbacks = sum(1 for row in rows if row.fallback_used)
    invalid = sum(1 for row in rows if row.outcome == "invalid_output")

    cost_per_user_day: dict[str, int] = {}
    for row in rows:
        key = f"{row.user_id}:{row.created_at.date().isoformat()}"
        cost_per_user_day[key] = cost_per_user_day.get(key, 0) + row.cost_minor

    return GatewayMetrics(
        window_hours=window_hours,
        total_invocations=total,
        latency_p50_ms=_percentile(latencies, 0.50),
        latency_p95_ms=_percentile(latencies, 0.95),
        cache_hit_rate=(cache_hits / total) if total else None,
        fallback_rate=(fallbacks / total) if total else None,
        invalid_output_rate=(invalid / total) if total else None,
        cost_per_user_per_day_minor=cost_per_user_day,
    )
