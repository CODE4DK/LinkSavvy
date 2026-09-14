from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.plan_limits_seed import DEFAULT_PLAN_LIMITS
from app.models.plan_limit import PlanLimit

_EXPECTED_METRICS = {
    "ai_runs",
    "audits",
    "tool_runs",
    "assistant_messages",
    "saved_assets",
    "resume_analyses",
}


def test_seed_covers_every_metric_for_both_plans() -> None:
    by_metric_plan = {(row["metric"], row["plan"]) for row in DEFAULT_PLAN_LIMITS}
    assert {metric for metric, _ in by_metric_plan} == _EXPECTED_METRICS
    for metric in _EXPECTED_METRICS:
        assert (metric, "free") in by_metric_plan
        assert (metric, "pro") in by_metric_plan


def test_pro_limit_is_never_smaller_than_free_for_the_same_metric() -> None:
    by_metric: dict[str, dict[str, int]] = {}
    for row in DEFAULT_PLAN_LIMITS:
        by_metric.setdefault(row["metric"], {})[row["plan"]] = row["limit_value"]
    for metric, plans in by_metric.items():
        assert plans["pro"] >= plans["free"], metric


async def test_db_session_fixture_seeds_plan_limits(db_session: AsyncSession) -> None:
    rows = (await db_session.execute(select(PlanLimit))).scalars().all()
    assert len(rows) == len(DEFAULT_PLAN_LIMITS)
