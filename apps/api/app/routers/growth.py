"""The Growth Hub's HTTP surface: the four scores, the current weekly
plan (with per-item completion), and the active growth goal. See
app/growth/service.py, app/growth/weekly_plan.py, and app/growth/goals.py
for the domain logic.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant import orchestrator
from app.assistant.presenters import to_conversation_summary, to_message_response
from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.growth import coach as coach_service
from app.growth import goals as goals_service
from app.growth import history as history_service
from app.growth.schema import GrowthScore
from app.growth.service import get_growth_scores
from app.growth.weekly_plan import get_current_plan, set_item_completed
from app.models.growth_goal import GrowthGoal
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan
from app.schemas.assistant import ConversationSummary, MessageResponse, SendMessageRequest
from app.schemas.growth import (
    BeforeAfterProfileEditResponse,
    BeforeAfterResponse,
    BeforeAfterToolRunResponse,
    GrowthGoalCreate,
    GrowthGoalResponse,
    GrowthScoreHistoryResponse,
    GrowthScoreResponse,
    GrowthScoresResponse,
    ScoreComponentResponse,
    ScoreDeltaResponse,
    ScoreHistoryPointResponse,
    WeeklyPlanItemUpdate,
    WeeklyPlanResponse,
)

_DEFAULT_HISTORY_MONTHS = 6

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


@router.get("/coach/conversation", response_model=ConversationSummary)
async def get_coach_conversation_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummary:
    """Gets or creates the user's one ongoing `mode="coach"` conversation
    -- the shared Assistant conversation store's answer to "which thread
    does /hubs/growth/coach open" (see docs/adr/0010). Sending and
    reading messages in it goes through the same generic
    `/api/v1/assistant/conversations/{id}/messages` endpoints every other
    conversation uses; this is the one growth-specific piece: knowing
    which conversation that is."""
    conversation = await coach_service.get_or_create_conversation(db, user=user)
    return to_conversation_summary(conversation)


@router.post("/coach/messages", response_model=MessageResponse)
async def send_coach_message_endpoint(
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """A convenience alias for sending into the coach conversation
    without the frontend first fetching its id -- routes through the same
    `orchestrator.handle_message` every conversation uses (mode="coach"
    dispatches straight to `coach_service.send_message`), so this still
    enforces the `assistant_messages` quota exactly like sending through
    `/api/v1/assistant/conversations/{coach_conversation_id}/messages`
    directly would."""
    conversation = await coach_service.get_or_create_conversation(db, user=user)
    result = await orchestrator.handle_message(
        db, user=user, conversation=conversation, text=payload.text
    )
    return to_message_response(result.message)


@router.get("/scores/history", response_model=GrowthScoreHistoryResponse)
async def get_score_history_endpoint(
    months: int = Query(default=_DEFAULT_HISTORY_MONTHS, ge=1, le=24),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrowthScoreHistoryResponse:
    since = datetime.now(UTC).date() - timedelta(days=months * 30)
    history = await history_service.get_score_history(db, user_id=user.id, since=since)
    return GrowthScoreHistoryResponse(
        **{
            score_type: [
                ScoreHistoryPointResponse(snapshot_date=row.snapshot_date, value=row.value)
                for row in rows
            ]
            for score_type, rows in history.items()
        }
    )


@router.get("/before-after", response_model=BeforeAfterResponse)
async def get_before_after_endpoint(
    from_date: date = Query(...),
    to_date: date = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BeforeAfterResponse:
    if from_date > to_date:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "from_date must not be after to_date.")
    result = await history_service.get_before_after(
        db, user_id=user.id, from_date=from_date, to_date=to_date
    )
    return BeforeAfterResponse(
        from_date=result["from_date"],
        to_date=result["to_date"],
        score_deltas=[ScoreDeltaResponse(**d) for d in result["score_deltas"]],
        tool_runs=[BeforeAfterToolRunResponse(**r) for r in result["tool_runs"]],
        profile_edits=[BeforeAfterProfileEditResponse(**e) for e in result["profile_edits"]],
    )
