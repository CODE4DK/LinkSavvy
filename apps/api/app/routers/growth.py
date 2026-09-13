"""The Growth Hub's HTTP surface: the four scores, the current weekly
plan (with per-item completion), and the active growth goal. See
app/growth/service.py, app/growth/weekly_plan.py, and app/growth/goals.py
for the domain logic.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.growth import goals as goals_service
from app.growth.schema import GrowthScore
from app.growth.service import get_growth_scores
from app.growth.weekly_plan import get_current_plan, set_item_completed
from app.models.growth_goal import GrowthGoal
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan
from app.schemas.growth import (
    GrowthGoalCreate,
    GrowthGoalResponse,
    GrowthScoreResponse,
    GrowthScoresResponse,
    ScoreComponentResponse,
    WeeklyPlanItemUpdate,
    WeeklyPlanResponse,
)

router = APIRouter(prefix="/api/v1/growth", tags=["growth"])


def _score_to_response(score: GrowthScore) -> GrowthScoreResponse:
    return GrowthScoreResponse(
        score_type=score.score_type.value,
        value=score.value,
        status=score.status.value,
        components=[
            ScoreComponentResponse(name=c.name, weight=c.weight, value=c.value, evidence=c.evidence)
            for c in score.components
        ],
        computed_at=score.computed_at,
        scoring_version=score.scoring_version,
        needed=score.needed,
    )


def _plan_to_response(plan: WeeklyPlan) -> WeeklyPlanResponse:
    return WeeklyPlanResponse(
        id=str(plan.id),
        week_start=plan.week_start,
        generated_at=plan.generated_at,
        focus=plan.focus,
        items=plan.items,  # type: ignore[arg-type]
        status=plan.status,
        completed_count=plan.completed_count,
        reflection=plan.reflection,
    )


def _goal_to_response(goal: GrowthGoal) -> GrowthGoalResponse:
    return GrowthGoalResponse(
        id=str(goal.id),
        goal_type=goal.goal_type,
        target_role=goal.target_role,
        target_description=goal.target_description,
        horizon_weeks=goal.horizon_weeks,
        started_at=goal.started_at,
        status=goal.status,  # type: ignore[arg-type]
        baseline_scores=goal.baseline_scores,
    )


@router.get("/scores", response_model=GrowthScoresResponse)
async def get_scores_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrowthScoresResponse:
    scores = await get_growth_scores(db, user=user)
    return GrowthScoresResponse(
        health=_score_to_response(scores["health"]),
        visibility=_score_to_response(scores["visibility"]),
        consistency=_score_to_response(scores["consistency"]),
        personal_branding=_score_to_response(scores["personal_branding"]),
    )


@router.get("/plan", response_model=WeeklyPlanResponse)
async def get_current_plan_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanResponse:
    plan = await get_current_plan(db, user=user)
    if plan is None:
        raise ApiError(ErrorCode.NOT_FOUND, "No weekly plan has been generated for this week yet.")
    return _plan_to_response(plan)


@router.patch("/plan/{plan_id}/items/{item_index}", response_model=WeeklyPlanResponse)
async def update_plan_item_endpoint(
    plan_id: uuid.UUID,
    item_index: int,
    payload: WeeklyPlanItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanResponse:
    try:
        plan = await set_item_completed(
            db,
            user_id=user.id,
            plan_id=plan_id,
            item_index=item_index,
            completed=payload.completed,
        )
    except (LookupError, IndexError) as exc:
        raise ApiError(ErrorCode.NOT_FOUND, str(exc)) from exc
    return _plan_to_response(plan)


@router.get("/goal", response_model=GrowthGoalResponse)
async def get_active_goal_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrowthGoalResponse:
    goal = await goals_service.get_active_goal(db, user_id=user.id)
    if goal is None:
        raise ApiError(ErrorCode.NOT_FOUND, "No active growth goal has been set yet.")
    return _goal_to_response(goal)


@router.post("/goal", response_model=GrowthGoalResponse)
async def start_goal_endpoint(
    payload: GrowthGoalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrowthGoalResponse:
    scores = await get_growth_scores(db, user=user)
    baseline_scores = {key: score.value for key, score in scores.items()}
    goal = await goals_service.start_goal(
        db,
        user=user,
        goal_type=payload.goal_type,
        target_role=payload.target_role,
        target_description=payload.target_description,
        horizon_weeks=payload.horizon_weeks,
        baseline_scores=baseline_scores,
    )
    return _goal_to_response(goal)
