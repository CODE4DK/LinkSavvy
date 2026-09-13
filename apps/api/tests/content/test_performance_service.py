from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.content import calendar_service, performance_service
from app.models.user import User
from app.schemas.content_plans import ContentPlanCreate, PerformanceNumbers


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"perf-{uuid.uuid4()}@example.com", full_name="Performance Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_record_performance_merges_into_existing_data(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session, user=user, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
    )
    await performance_service.record_performance(
        db_session, user=user, plan_id=plan.id, numbers=PerformanceNumbers(impressions=1000)
    )
    updated = await performance_service.record_performance(
        db_session, user=user, plan_id=plan.id, numbers=PerformanceNumbers(reactions=20)
    )
    assert updated.performance == {"impressions": 1000, "reactions": 20}


async def test_summary_reports_insufficient_data_below_threshold(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    for _ in range(3):
        plan = await calendar_service.create_plan(
            db_session, user=user, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
        )
        await performance_service.record_performance(
            db_session, user=user, plan_id=plan.id, numbers=PerformanceNumbers(reactions=10)
        )

    sufficient, total, by_type = await performance_service.performance_summary(
        db_session, user=user
    )
    assert sufficient is False
    assert total == 3
    assert by_type == []


async def test_summary_computes_median_engagement_by_content_type(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    post_engagements = [10, 20, 30]
    for reactions in post_engagements:
        plan = await calendar_service.create_plan(
            db_session,
            user=user,
            payload=ContentPlanCreate(content_type="post", planned_for=date(2026, 6, 1)),
        )
        await performance_service.record_performance(
            db_session, user=user, plan_id=plan.id, numbers=PerformanceNumbers(reactions=reactions)
        )
    for reactions in [100, 200]:
        plan = await calendar_service.create_plan(
            db_session,
            user=user,
            payload=ContentPlanCreate(content_type="carousel", planned_for=date(2026, 6, 1)),
        )
        await performance_service.record_performance(
            db_session, user=user, plan_id=plan.id, numbers=PerformanceNumbers(reactions=reactions)
        )

    sufficient, total, by_type = await performance_service.performance_summary(
        db_session, user=user
    )
    assert sufficient is True
    assert total == 5
    by_type_map = {ct: (n, median) for ct, n, median in by_type}
    assert by_type_map["post"] == (3, 20.0)
    assert by_type_map["carousel"] == (2, 150.0)


async def test_summary_ignores_plans_with_no_engagement_data(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    for _ in range(6):
        plan = await calendar_service.create_plan(
            db_session, user=user, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
        )
        # Only impressions -- not an engagement signal, so this shouldn't count.
        await performance_service.record_performance(
            db_session, user=user, plan_id=plan.id, numbers=PerformanceNumbers(impressions=500)
        )

    sufficient, total, _ = await performance_service.performance_summary(db_session, user=user)
    assert sufficient is False
    assert total == 0
