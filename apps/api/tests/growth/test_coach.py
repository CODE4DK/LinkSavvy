from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.growth import coach
from app.growth.goals import get_active_goal
from app.models.growth_score_snapshot import GrowthScoreSnapshot
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-coach-{uuid.uuid4()}@example.com", full_name="Coach Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _fake_gateway_result(parsed: dict[str, Any]) -> gateway.GatewayResult:
    return gateway.GatewayResult(
        text=None,
        parsed=parsed,
        model="fake-model",
        provider="fake",
        tokens_in=1,
        tokens_out=1,
        cost_minor=0,
        currency="usd",
        latency_ms=0.0,
        cached=False,
        fallback_used=False,
        correlation_id="corr-1",
        invocation_id=uuid.uuid4(),
    )


async def test_get_or_create_conversation_is_idempotent(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    first = await coach.get_or_create_conversation(db_session, user=user)
    second = await coach.get_or_create_conversation(db_session, user=user)
    assert first.id == second.id
    assert first.mode == "coach"


async def test_first_message_uses_the_interviewing_fixture(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    conversation = await coach.get_or_create_conversation(db_session, user=user)

    reply = await coach.send_message(db_session, user=user, conversation=conversation, text="Hi")

    assert reply.role == "assistant"
    assert reply.tool_call is not None
    assert reply.tool_call["phase"] == "interviewing"
    messages = await coach.list_messages(db_session, conversation_id=conversation.id)
    assert [m.role for m in messages] == ["user", "assistant"]


async def test_planning_phase_starts_a_goal_and_sets_coach_state(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await coach.get_or_create_conversation(db_session, user=user)

    async def _fake_run(*args: Any, **kwargs: Any) -> gateway.GatewayResult:
        return _fake_gateway_result(
            {
                "reply": "Here's your plan.",
                "phase": "planning",
                "interview_complete": True,
                "questions_asked": 3,
                "score_movement": "not_enough_history",
                "working_plan": {
                    "goal_type": "role_change",
                    "target_role": "Staff Engineer",
                    "horizon_weeks": 12,
                    "phases": [
                        {"name": "Foundation", "focus": "Fix profile basics", "duration_weeks": 4}
                    ],
                },
                "proposed_tool_id": None,
            }
        )

    monkeypatch.setattr(gateway, "run", _fake_run)

    await coach.send_message(
        db_session, user=user, conversation=conversation, text="I want to become a Staff Engineer."
    )

    goal = await get_active_goal(db_session, user_id=user.id)
    assert goal is not None
    assert goal.goal_type == "role_change"
    assert goal.target_role == "Staff Engineer"
    assert goal.coach_state is not None
    assert goal.coach_state["phases"][0]["name"] == "Foundation"


async def test_progress_since_last_visit_is_honest_about_missing_history(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    last_visit = datetime.now(UTC) - timedelta(days=5)

    text = await coach._progress_since_last_visit(
        db_session, user=user, prior_last_message_at=last_visit
    )
    assert "No score history is available to compare yet." in text
    assert "No tools were run since then." in text
    assert "No weekly-plan items were marked complete since then." in text


async def test_progress_since_last_visit_reports_real_movement_for_every_score(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    last_visit = datetime.now(UTC) - timedelta(days=3)

    db_session.add_all(
        [
            GrowthScoreSnapshot(
                user_id=user.id,
                score_type="health",
                value=70,
                status="needs_attention",
                scoring_version="2026.1",
                snapshot_date=(last_visit - timedelta(days=1)).date(),
            ),
            GrowthScoreSnapshot(
                user_id=user.id,
                score_type="health",
                value=75,
                status="needs_attention",
                scoring_version="2026.1",
                snapshot_date=datetime.now(UTC).date(),
            ),
            GrowthScoreSnapshot(
                user_id=user.id,
                score_type="visibility",
                value=60,
                status="needs_attention",
                scoring_version="2026.1",
                snapshot_date=(last_visit - timedelta(days=1)).date(),
            ),
            GrowthScoreSnapshot(
                user_id=user.id,
                score_type="visibility",
                value=60,
                status="needs_attention",
                scoring_version="2026.1",
                snapshot_date=datetime.now(UTC).date(),
            ),
        ]
    )
    db_session.add(
        WeeklyPlan(
            user_id=user.id,
            week_start=datetime.now(UTC).date(),
            generated_at=datetime.now(UTC),
            focus="",
            items=[],
            status="active",
            completed_count=2,
        )
    )
    await db_session.commit()

    text = await coach._progress_since_last_visit(
        db_session, user=user, prior_last_message_at=last_visit
    )
    assert "Health up 5 to 75" in text
    assert "Visibility unchanged at 60" in text
    assert "2 weekly-plan item(s) were marked complete" in text


async def test_first_visit_has_no_progress_note(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    text = await coach._progress_since_last_visit(db_session, user=user, prior_last_message_at=None)
    assert text == "This is the user's first time using the Growth Coach."
