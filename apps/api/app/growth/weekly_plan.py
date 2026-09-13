"""The weekly recommendation engine: 3-5 items drawn from the user's own
latest audit recommendations (already a deterministic, ranked table --
see app.audit.recommendations -- so this reuses that ranking rather than
inventing a second one), the active growth goal (for framing, not for
picking which items), and last week's plan (for the retrospective).

Deliberately never AI-generated: the items, their impact estimates, and
their explanations all come from the same fixed table the Audit Engine's
own recommendations already use.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import list_recommendations
from app.growth.goals import get_active_goal
from app.models.recommendation import Recommendation
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan

_MAX_ITEMS = 5
_QUICK_THRESHOLD_MINUTES = 10
_ESTIMATED_MINUTES_BY_CATEGORY: dict[str, int] = {
    "visibility": 8,
    "engagement": 8,
    "profile": 20,
    "content": 25,
    "career": 30,
}
_DEFAULT_ESTIMATED_MINUTES = 20


def current_week_start(*, now_local: datetime) -> date:
    today = now_local.date()
    return today - timedelta(days=today.weekday())


def _estimated_minutes(recommendation: Recommendation) -> int:
    return _ESTIMATED_MINUTES_BY_CATEGORY.get(recommendation.category, _DEFAULT_ESTIMATED_MINUTES)


def _build_item(recommendation: Recommendation) -> dict[str, Any]:
    return {
        "title": recommendation.title,
        "why_now": recommendation.why,
        "tool_id": recommendation.action_tool_id,
        "estimated_minutes": _estimated_minutes(recommendation),
        "expected_impact": recommendation.estimated_impact_points,
        "category": recommendation.category,
        "completed": False,
    }


async def _select_items(db: AsyncSession, *, user_id: uuid.UUID) -> list[dict[str, Any]]:
    open_recommendations = await list_recommendations(
        db, user_id=user_id, status="open", cursor=None, limit=50
    )
    if not open_recommendations:
        return []

    chosen = open_recommendations[:_MAX_ITEMS]
    items = [_build_item(rec) for rec in chosen]

    has_quick_item = any(item["estimated_minutes"] < _QUICK_THRESHOLD_MINUTES for item in items)
    if not has_quick_item:
        quick_candidate = next(
            (
                rec
                for rec in open_recommendations
                if _estimated_minutes(rec) < _QUICK_THRESHOLD_MINUTES
            ),
            None,
        )
        if quick_candidate is not None:
            items[-1] = _build_item(quick_candidate)

    return items


def _focus_text(goal: Any) -> str:
    if goal is None:
        return "Keep steadily improving your LinkedIn presence this week."
    if goal.target_role:
        return f"Building toward {goal.target_role}."
    return "Making progress on your growth goal this week."


async def _reflect_on_previous_week(
    db: AsyncSession, *, user_id: uuid.UUID, week_start: date
) -> None:
    previous_week_start = week_start - timedelta(days=7)
    result = await db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.week_start == previous_week_start,
            WeeklyPlan.status == "active",
        )
    )
    previous_plan = result.scalar_one_or_none()
    if previous_plan is None:
        return

    items = previous_plan.items
    completed = [item["title"] for item in items if item.get("completed")]
    not_completed = [item["title"] for item in items if not item.get("completed")]
    previous_plan.reflection = {
        "moved": completed,
        "did_not_move": not_completed,
        "carry_forward": not_completed,
        "completion_rate": (round(len(completed) / len(items), 2) if items else None),
    }
    previous_plan.status = "reflected"


def _local_now(user: User) -> datetime:
    try:
        tz: tzinfo = ZoneInfo(user.timezone)
    except ZoneInfoNotFoundError:
        tz = UTC
    return datetime.now(tz)


async def generate_plan_for_user(db: AsyncSession, *, user: User) -> WeeklyPlan:
    week_start = current_week_start(now_local=_local_now(user))

    existing = await get_plan_for_week(db, user_id=user.id, week_start=week_start)
    if existing is not None:
        return existing

    await _reflect_on_previous_week(db, user_id=user.id, week_start=week_start)

    goal = await get_active_goal(db, user_id=user.id)
    items = await _select_items(db, user_id=user.id)

    plan = WeeklyPlan(
        user_id=user.id,
        week_start=week_start,
        generated_at=datetime.now(UTC),
        focus=_focus_text(goal),
        items=items,
        status="active",
        completed_count=0,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def get_plan_for_week(
    db: AsyncSession, *, user_id: uuid.UUID, week_start: date
) -> WeeklyPlan | None:
    result = await db.execute(
        select(WeeklyPlan).where(WeeklyPlan.user_id == user_id, WeeklyPlan.week_start == week_start)
    )
    return result.scalar_one_or_none()


async def get_current_plan(db: AsyncSession, *, user: User) -> WeeklyPlan | None:
    week_start = current_week_start(now_local=_local_now(user))
    return await get_plan_for_week(db, user_id=user.id, week_start=week_start)


async def set_item_completed(
    db: AsyncSession, *, user_id: uuid.UUID, plan_id: uuid.UUID, item_index: int, completed: bool
) -> WeeklyPlan:
    plan = await db.get(WeeklyPlan, plan_id)
    if plan is None or plan.user_id != user_id:
        raise LookupError(f"no weekly plan {plan_id} for this user")
    if item_index < 0 or item_index >= len(plan.items):
        raise IndexError(f"weekly plan {plan_id} has no item at index {item_index}")

    items = list(plan.items)
    items[item_index] = {**items[item_index], "completed": completed}
    plan.items = items
    plan.completed_count = sum(1 for item in items if item.get("completed"))
    await db.commit()
    await db.refresh(plan)
    return plan
