from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.weekly_plan import (
    current_week_start,
    generate_plan_for_user,
    get_plan_for_week,
    set_item_completed,
)
from app.models.audit import Audit
from app.models.recommendation import Recommendation
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(
        email=f"growth-plan-{uuid.uuid4()}@example.com",
        full_name="Plan Tester",
        timezone="UTC",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _seed_audit(db: AsyncSession, *, user: User) -> Audit:
    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    return audit


async def _add_recommendation(
    db: AsyncSession,
    *,
    user: User,
    audit: Audit,
    priority: int,
    category: str,
    title: str,
    tool_id: str | None = None,
    impact: int = 5,
) -> Recommendation:
    rec = Recommendation(
        audit_id=audit.id,
        user_id=user.id,
        category=category,
        priority=priority,
        title=title,
        why=f"Why {title} matters right now.",
        action_label="Fix it",
        action_route="/profile",
        action_tool_id=tool_id,
        estimated_impact_points=impact,
        status="open",
    )
    db.add(rec)
    await db.commit()
    return rec


async def test_no_recommendations_produces_an_empty_plan(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await generate_plan_for_user(db_session, user=user)
    assert plan.items == []
    assert plan.status == "active"


async def test_selects_up_to_five_items_ranked_by_priority(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = await _seed_audit(db_session, user=user)
    for i in range(8):
        await _add_recommendation(
            db_session,
            user=user,
            audit=audit,
            priority=i,
            category="profile",
            title=f"Item {i}",
        )

    plan = await generate_plan_for_user(db_session, user=user)
    assert len(plan.items) == 5
    assert [item["title"] for item in plan.items] == [f"Item {i}" for i in range(5)]
    for item in plan.items:
        assert item["completed"] is False
        assert item["why_now"]


async def test_guarantees_at_least_one_item_under_ten_minutes(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = await _seed_audit(db_session, user=user)
    # Five slow (career, 30 min) recommendations ranked ahead of one quick
    # (visibility, 8 min) one -- the quick one should still make the cut.
    for i in range(5):
        await _add_recommendation(
            db_session, user=user, audit=audit, priority=i, category="career", title=f"Slow {i}"
        )
    await _add_recommendation(
        db_session, user=user, audit=audit, priority=5, category="visibility", title="Quick fix"
    )

    plan = await generate_plan_for_user(db_session, user=user)
    assert len(plan.items) == 5
    assert any(item["estimated_minutes"] < 10 for item in plan.items)
    assert any(item["title"] == "Quick fix" for item in plan.items)


async def test_is_idempotent_for_the_same_week(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = await _seed_audit(db_session, user=user)
    await _add_recommendation(
        db_session, user=user, audit=audit, priority=0, category="profile", title="Only item"
    )

    first = await generate_plan_for_user(db_session, user=user)
    second = await generate_plan_for_user(db_session, user=user)
    assert first.id == second.id


async def test_completing_items_updates_the_count(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = await _seed_audit(db_session, user=user)
    await _add_recommendation(
        db_session, user=user, audit=audit, priority=0, category="profile", title="A"
    )
    await _add_recommendation(
        db_session, user=user, audit=audit, priority=1, category="profile", title="B"
    )
    plan = await generate_plan_for_user(db_session, user=user)
    assert plan.completed_count == 0

    updated = await set_item_completed(
        db_session, user_id=user.id, plan_id=plan.id, item_index=0, completed=True
    )
    assert updated.completed_count == 1
    assert updated.items[0]["completed"] is True
    assert updated.items[1]["completed"] is False


async def test_reflects_on_the_previous_week_when_generating_the_next(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    audit = await _seed_audit(db_session, user=user)
    await _add_recommendation(
        db_session, user=user, audit=audit, priority=0, category="profile", title="Done thing"
    )
    await _add_recommendation(
        db_session, user=user, audit=audit, priority=1, category="profile", title="Undone thing"
    )

    last_week_start = current_week_start(now_local=datetime.now(UTC)) - timedelta(days=7)
    from app.models.weekly_plan import WeeklyPlan

    previous = WeeklyPlan(
        user_id=user.id,
        week_start=last_week_start,
        generated_at=datetime.now(UTC),
        focus="Last week's focus",
        items=[
            {
                "title": "Done thing",
                "why_now": "x",
                "tool_id": None,
                "estimated_minutes": 10,
                "expected_impact": 5,
                "category": "profile",
                "completed": True,
            },
            {
                "title": "Undone thing",
                "why_now": "x",
                "tool_id": None,
                "estimated_minutes": 10,
                "expected_impact": 5,
                "category": "profile",
                "completed": False,
            },
        ],
        status="active",
        completed_count=1,
    )
    db_session.add(previous)
    await db_session.commit()

    await generate_plan_for_user(db_session, user=user)

    await db_session.refresh(previous)
    assert previous.status == "reflected"
    assert previous.reflection is not None
    assert previous.reflection["moved"] == ["Done thing"]
    assert previous.reflection["did_not_move"] == ["Undone thing"]
    assert previous.reflection["carry_forward"] == ["Undone thing"]


async def test_get_plan_for_week_returns_none_when_not_generated(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    week_start = current_week_start(now_local=datetime.now(UTC))
    assert await get_plan_for_week(db_session, user_id=user.id, week_start=week_start) is None
