"""The AI Growth Coach: a conversational surface built directly on the
gateway (see growth.coach.v1.prompt.md), absorbed into the Phase 9
Assistant's shared conversation store as `mode="coach"` (see
app/assistant/conversations.py and docs/adr/0010) rather than keeping
its own session/message tables -- `/hubs/growth/coach` stays a distinct
frontend route and this module still owns its own prompt and honesty
mechanism, but every message it writes is an ordinary `Message` row like
any other conversation. Every turn re-sends the user's real current
scores and real progress since their last visit so the model can never
manufacture a "you're doing great!" that the data doesn't support.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.assistant.conversations import (
    append_message,
    get_or_create_active_conversation,
    get_thread,
)
from app.assistant.summarize import conversation_history_text
from app.growth import history as history_service
from app.growth.goals import get_active_goal, goal_summary, start_goal
from app.growth.schema import GrowthScore
from app.growth.service import get_growth_scores
from app.models.conversation import Conversation
from app.models.growth_goal import GrowthGoal
from app.models.message import Message
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan

_SCORE_LABELS: dict[str, str] = {
    "health": "Health",
    "visibility": "Visibility",
    "consistency": "Consistency",
    "personal_branding": "Personal Branding",
}

_PROMPT_ID = "growth.coach.v1"
_MODE = "coach"


async def get_or_create_conversation(db: AsyncSession, *, user: User) -> Conversation:
    return await get_or_create_active_conversation(db, user=user, mode=_MODE)


async def list_messages(db: AsyncSession, *, conversation_id: Any) -> list[Message]:
    return await get_thread(db, conversation_id=conversation_id)


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

    now = datetime.now(UTC)
    days = max(0, (now - prior_last_message_at).days)
    parts = [f"{days} day(s) since the user's last coach visit."]

    before_after = await history_service.get_before_after(
        db,
        user_id=user.id,
        from_date=prior_last_message_at.date(),
        to_date=now.date(),
    )

    movements = []
    for delta in before_after["score_deltas"]:
        label = _SCORE_LABELS[delta["score_type"]]
        if delta["delta"] is not None and delta["delta"] != 0:
            direction = "up" if delta["delta"] > 0 else "down"
            movements.append(f"{label} {direction} {abs(delta['delta'])} to {delta['to_value']}")
        elif delta["delta"] == 0:
            movements.append(f"{label} unchanged at {delta['to_value']}")
        elif delta["to_value"] is not None:
            movements.append(f"{label} is {delta['to_value']} (no snapshot from before then)")
    if movements:
        parts.append("Real score movement since then: " + "; ".join(movements) + ".")
    else:
        parts.append("No score history is available to compare yet.")

    if before_after["tool_runs"]:
        parts.append(f"{len(before_after['tool_runs'])} tool run(s) happened since then.")
    else:
        parts.append("No tools were run since then.")

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

    return " ".join(parts)


async def send_message(
    db: AsyncSession, *, user: User, conversation: Conversation, text: str
) -> Message:
    prior_messages = await get_thread(db, conversation_id=conversation.id)
    prior_last_message_at = conversation.last_message_at
    prior_leaf_id = prior_messages[-1].id if prior_messages else None

    goal = await get_active_goal(db, user_id=user.id)

    user_message = await append_message(
        db, conversation=conversation, role="user", content=text, parent_message_id=prior_leaf_id
    )

    scores = await get_growth_scores(db, user=user)
    context = {
        "goal_summary": goal_summary(goal),
        "scores_summary": _scores_summary(scores),
        "progress_since_last_visit": await _progress_since_last_visit(
            db, user=user, prior_last_message_at=prior_last_message_at
        ),
        "conversation_history": conversation_history_text(prior_messages, assistant_label="Coach"),
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
        else:
            goal = await db.get(GrowthGoal, goal.id)
            assert goal is not None
        goal.coach_state = working_plan
        await db.commit()

    return await append_message(
        db,
        conversation=conversation,
        role="assistant",
        content=parsed["reply"],
        parent_message_id=user_message.id,
        tool_call={
            "phase": parsed["phase"],
            "proposed_tool_id": parsed.get("proposed_tool_id"),
            "score_movement": parsed["score_movement"],
        },
    )
