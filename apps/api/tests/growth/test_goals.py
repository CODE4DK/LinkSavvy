from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth import goals
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-goal-{uuid.uuid4()}@example.com", full_name="Goal Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_no_active_goal_by_default(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    assert await goals.get_active_goal(db_session, user_id=user.id) is None


async def test_starting_a_goal_makes_it_active(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    goal = await goals.start_goal(
        db_session,
        user=user,
        goal_type="role_change",
        target_role="Staff Engineer",
        target_description="Move into a staff-level backend role.",
        horizon_weeks=12,
        baseline_scores={"visibility": 50},
    )
    assert goal.status == "active"
    active = await goals.get_active_goal(db_session, user_id=user.id)
    assert active is not None
    assert active.id == goal.id


async def test_starting_a_new_goal_retires_the_old_one(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    first = await goals.start_goal(
        db_session,
        user=user,
        goal_type="role_change",
        target_role="Staff Engineer",
        target_description="",
        horizon_weeks=12,
        baseline_scores={},
    )
    second = await goals.start_goal(
        db_session,
        user=user,
        goal_type="visibility",
        target_role=None,
        target_description="Get more visible.",
        horizon_weeks=8,
        baseline_scores={},
    )

    await db_session.refresh(first)
    assert first.status == "abandoned"
    active = await goals.get_active_goal(db_session, user_id=user.id)
    assert active is not None
    assert active.id == second.id


async def test_complete_and_abandon_goal(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    goal = await goals.start_goal(
        db_session,
        user=user,
        goal_type="role_change",
        target_role=None,
        target_description="",
        horizon_weeks=4,
        baseline_scores={},
    )
    completed = await goals.complete_goal(db_session, user_id=user.id, goal_id=goal.id)
    assert completed.status == "completed"
    assert await goals.get_active_goal(db_session, user_id=user.id) is None
