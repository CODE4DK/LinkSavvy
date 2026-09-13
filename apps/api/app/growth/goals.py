"""Growth goal CRUD. A user has at most one *active* goal at a time --
enforced here in the service layer (MySQL has no partial unique index to
lean on) rather than by a database constraint: starting a new goal
retires the old one instead of leaving two "active" rows to disagree
about which one the weekly plan and the coach should anchor to.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_goal import GrowthGoal
from app.models.user import User


async def get_active_goal(db: AsyncSession, *, user_id: uuid.UUID) -> GrowthGoal | None:
    result = await db.execute(
        select(GrowthGoal)
        .where(
            GrowthGoal.user_id == user_id,
            GrowthGoal.status == "active",
            GrowthGoal.deleted_at.is_(None),
        )
        .order_by(GrowthGoal.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def start_goal(
    db: AsyncSession,
    *,
    user: User,
    goal_type: str,
    target_role: str | None,
    target_description: str,
    horizon_weeks: int,
    baseline_scores: dict[str, Any],
) -> GrowthGoal:
    existing = await get_active_goal(db, user_id=user.id)
    if existing is not None:
        existing.status = "abandoned"

    goal = GrowthGoal(
        user_id=user.id,
        goal_type=goal_type,
        target_role=target_role,
        target_description=target_description,
        horizon_weeks=horizon_weeks,
        started_at=datetime.now(UTC),
        status="active",
        baseline_scores=baseline_scores,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def complete_goal(db: AsyncSession, *, user_id: uuid.UUID, goal_id: uuid.UUID) -> GrowthGoal:
    goal = await _get_owned_goal(db, user_id=user_id, goal_id=goal_id)
    goal.status = "completed"
    await db.commit()
    await db.refresh(goal)
    return goal


async def abandon_goal(db: AsyncSession, *, user_id: uuid.UUID, goal_id: uuid.UUID) -> GrowthGoal:
    goal = await _get_owned_goal(db, user_id=user_id, goal_id=goal_id)
    goal.status = "abandoned"
    await db.commit()
    await db.refresh(goal)
    return goal


async def _get_owned_goal(
    db: AsyncSession, *, user_id: uuid.UUID, goal_id: uuid.UUID
) -> GrowthGoal:
    goal = await db.get(GrowthGoal, goal_id)
    if goal is None or goal.user_id != user_id or goal.deleted_at is not None:
        raise LookupError(f"no growth goal {goal_id} for this user")
    return goal
