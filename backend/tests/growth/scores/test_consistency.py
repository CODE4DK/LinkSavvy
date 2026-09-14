from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.schema import GrowthScoreStatus
from app.growth.scores.consistency import get_consistency_score
from app.models.content_plan import ContentPlan
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-cons-{uuid.uuid4()}@example.com", full_name="Consistency Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _this_monday() -> datetime:
    today = datetime.now(UTC).date()
    monday = today - timedelta(days=today.weekday())
    return datetime(monday.year, monday.month, monday.day, 9, tzinfo=UTC)


async def _add_post(db: AsyncSession, *, user: User, weeks_ago: int, day_offset: int = 1) -> None:
    posted_at = _this_monday() - timedelta(weeks=weeks_ago) + timedelta(days=day_offset)
    db.add(
        ContentPlan(
            user_id=user.id,
            title="A post",
            planned_for=posted_at.date(),
            status="posted",
            posted_at=posted_at,
        )
    )
    await db.commit()


async def test_insufficient_data_with_fewer_than_four_active_weeks(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _add_post(db_session, user=user, weeks_ago=0)
    await _add_post(db_session, user=user, weeks_ago=1)

    score = await get_consistency_score(db_session, user=user)
    assert score.status == GrowthScoreStatus.INSUFFICIENT_DATA
    assert score.value is None
    assert score.needed == {
        "weeks_with_activity": 2,
        "weeks_needed": 4,
        "reason": "Record at least four weeks of posts to unlock this score.",
    }


async def test_scores_a_streak_at_the_front_of_the_window(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    for weeks_ago in (0, 1, 2, 3):
        await _add_post(db_session, user=user, weeks_ago=weeks_ago)

    score = await get_consistency_score(db_session, user=user)
    assert score.status == GrowthScoreStatus.OK
    assert score.value is not None
    by_name = {c.name: c for c in score.components}

    assert by_name["longest_gap"].evidence["longest_gap_weeks"] == 8
    assert by_name["streak_length"].evidence["current_streak_weeks"] == 4
    assert by_name["posts_per_week"].evidence["average_posts_per_week"] == round(4 / 12, 2)

    for component in score.components:
        assert component.weight > 0
        assert component.evidence


async def test_a_steady_weekly_habit_scores_higher_than_a_bunched_one(
    db_session: AsyncSession,
) -> None:
    steady_user = await _create_user(db_session)
    for weeks_ago in range(12):
        await _add_post(db_session, user=steady_user, weeks_ago=weeks_ago)

    bunched_user = await _create_user(db_session)
    for weeks_ago in (0, 1, 2, 3):
        for day in range(3):
            await _add_post(db_session, user=bunched_user, weeks_ago=weeks_ago, day_offset=day)

    steady_score = await get_consistency_score(db_session, user=steady_user)
    bunched_score = await get_consistency_score(db_session, user=bunched_user)

    assert steady_score.value is not None
    assert bunched_score.value is not None
    assert steady_score.value > bunched_score.value
