"""The AI Growth Coach: a conversational surface built directly on the
gateway (see growth.coach.v1.prompt.md) -- separate from the Phase 9
assistant, which will later absorb this as a mode. Every turn re-sends
the user's real current scores and real progress since their last visit
so the model can never manufacture a "you're doing great!" that the data
doesn't support.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.growth.goals import get_active_goal, start_goal
from app.growth.schema import GrowthScore
from app.growth.service import get_growth_scores
from app.models.coach_message import CoachMessage
from app.models.coach_session import CoachSession
from app.models.growth_goal import GrowthGoal
from app.models.score_history import ScoreHistory
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan

_PROMPT_ID = "growth.coach.v1"
_MAX_HISTORY_MESSAGES = 20


async def get_or_create_session(db: AsyncSession, *, user: User) -> CoachSession:
    result = await db.execute(
        select(CoachSession)
        .where(CoachSession.user_id == user.id, CoachSession.status == "active")
        .order_by(CoachSession.started_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if session is not None:
        return session

    goal = await get_active_goal(db, user_id=user.id)
    session = CoachSession(
        user_id=user.id,
        goal_id=goal.id if goal else None,
        status="active",
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_messages(db: AsyncSession, *, session_id: uuid.UUID) -> list[CoachMessage]:
    result = await db.execute(
        select(CoachMessage)
        .where(CoachMessage.session_id == session_id)
        .order_by(CoachMessage.created_at.asc())
    )
    return list(result.scalars().all())


def _goal_summary(goal: GrowthGoal | None) -> str:
    if goal is None:
        return "No active growth goal has been set yet."
    parts = [f"Goal type: {goal.goal_type}."]
    if goal.target_role:
        parts.append(f"Target role: {goal.target_role}.")
    if goal.target_description:
        parts.append(f"Description: {goal.target_description}")
    parts.append(
        f"Horizon: {goal.horizon_weeks} weeks, started {goal.started_at.date().isoformat()}."
    )
    phases = (goal.coach_state or {}).get("phases") or []
    if phases:
        phase_text = "; ".join(
            f"{p['name']} ({p['duration_weeks']}w): {p['focus']}" for p in phases
        )
        parts.append(f"Working plan phases: {phase_text}.")
    return " ".join(parts)


def _scores_summary(scores: dict[str, GrowthScore]) -> str:
    lines = []
    for key, score in scores.items():
        if score.value is None:
            lines.append(f"{key}: {score.status.value} (no value yet).")
        else:
            lines.append(f"{key}: {score.value}/100 ({score.status.value}).")
    return " ".join(lines)


async def _progress_since_last_visit(
    db: AsyncSession, *, user: User, prior_last_message_at: datetime | None
) -> str:
    if prior_last_message_at is None:
        return "This is the user's first time using the Growth Coach."

    days = max(0, (datetime.now(UTC) - prior_last_message_at).days)
    parts = [f"{days} day(s) since the user's last coach visit."]

    audit_result = await db.execute(
        select(ScoreHistory)
        .where(
            ScoreHistory.user_id == user.id,
            ScoreHistory.recorded_at > prior_last_message_at,
        )
        .order_by(ScoreHistory.recorded_at.asc())
    )
    new_history = audit_result.scalars().all()
    if new_history:
        parts.append(
            f"A new audit ran since then; overall Health Score is now {new_history[-1].overall}."
        )
    else:
        parts.append("No new audit has run since the last visit.")

    plans_result = await db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.user_id == user.id, WeeklyPlan.updated_at > prior_last_message_at
        )
    )
    total_completed = sum(plan.completed_count for plan in plans_result.scalars().all())
    if total_completed:
        parts.append(f"{total_completed} weekly-plan item(s) were marked complete since then.")
    else:
        parts.append("No weekly-plan items were marked complete since then.")

    parts.append(
        "Only the Health Score has tracked history between visits right now; Visibility, "
        "Consistency, and Personal Branding show only their current values (see ADR 0009)."
    )
    return " ".join(parts)


def _conversation_history(messages: list[CoachMessage]) -> str:
    if not messages:
        return "(no messages yet)"
    lines = []
    for message in messages[-_MAX_HISTORY_MESSAGES:]:
        speaker = "User" if message.role == "user" else "Coach"
        lines.append(f"{speaker}: {message.content}")
    return "\n".join(lines)


async def send_message(
    db: AsyncSession, *, user: User, session: CoachSession, text: str
) -> CoachMessage:
    prior_messages = await list_messages(db, session_id=session.id)
    prior_last_message_at = session.last_message_at

    db.add(CoachMessage(session_id=session.id, role="user", content=text, metadata_={}))
    await db.commit()

    goal: GrowthGoal | None = None
    if session.goal_id is not None:
        goal = await db.get(GrowthGoal, session.goal_id)

    scores = await get_growth_scores(db, user=user)
    context = {
        "goal_summary": _goal_summary(goal),
        "scores_summary": _scores_summary(scores),
        "progress_since_last_visit": await _progress_since_last_visit(
            db, user=user, prior_last_message_at=prior_last_message_at
        ),
        "conversation_history": _conversation_history(prior_messages),
        "user_message": text,
    }

    result = await gateway.run(_PROMPT_ID, context, user=user, db=db)
    assert result.parsed is not None
    parsed: dict[str, Any] = result.parsed

    working_plan = parsed.get("working_plan")
    if parsed["phase"] == "planning" and working_plan is not None:
        if goal is None:
            goal = await start_goal(
                db,
                user=user,
                goal_type=working_plan["goal_type"],
                target_role=working_plan.get("target_role"),
                target_description=text,
                horizon_weeks=working_plan["horizon_weeks"],
                baseline_scores={key: score.value for key, score in scores.items()},
            )
            session.goal_id = goal.id
        goal.coach_state = working_plan

    assistant_message = CoachMessage(
        session_id=session.id,
        role="assistant",
        content=parsed["reply"],
        metadata_={
            "phase": parsed["phase"],
            "proposed_tool_id": parsed.get("proposed_tool_id"),
            "score_movement": parsed["score_movement"],
        },
    )
    db.add(assistant_message)
    session.last_message_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(assistant_message)
    return assistant_message
