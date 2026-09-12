"""The canonical free/pro limits, shared by the test suite's seed fixture.

Migration 0003 seeds the real `plan_limits` table with its own inline copy
of these same values (migrations are frozen snapshots and deliberately
never import application code — see migration 0001's own inline copy of
the default feature-flag keys for the same reason). This module is what
application code and tests use to know what "the default limits" are.
"""

from __future__ import annotations

from typing import TypedDict


class PlanLimitSeed(TypedDict):
    plan: str
    metric: str
    limit_value: int
    window: str
    overage_behaviour: str


DEFAULT_PLAN_LIMITS: list[PlanLimitSeed] = [
    {
        "plan": "free",
        "metric": "ai_runs",
        "limit_value": 20,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "ai_runs",
        "limit_value": 500,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "audits",
        "limit_value": 3,
        "window": "month",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "audits",
        "limit_value": 60,
        "window": "month",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "tool_runs",
        "limit_value": 15,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "tool_runs",
        "limit_value": 300,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "assistant_messages",
        "limit_value": 30,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "assistant_messages",
        "limit_value": 1000,
        "window": "day",
        "overage_behaviour": "block",
    },
    {
        "plan": "free",
        "metric": "saved_assets",
        "limit_value": 20,
        "window": "month",
        "overage_behaviour": "soft_warn",
    },
    {
        "plan": "pro",
        "metric": "saved_assets",
        "limit_value": 500,
        "window": "month",
        "overage_behaviour": "soft_warn",
    },
    {
        "plan": "free",
        "metric": "resume_analyses",
        "limit_value": 2,
        "window": "month",
        "overage_behaviour": "block",
    },
    {
        "plan": "pro",
        "metric": "resume_analyses",
        "limit_value": 50,
        "window": "month",
        "overage_behaviour": "block",
    },
]
