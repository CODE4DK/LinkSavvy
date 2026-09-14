from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.weekly_plan import generate_plan_for_user
from app.models.audit import Audit
from app.models.growth_score_snapshot import GrowthScoreSnapshot
from app.models.recommendation import Recommendation
from app.models.user import User
from app.notifications.weekly_digest import compose_weekly_digest, render_digest_body


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"digest-{uuid.uuid4()}@example.com", full_name="Digest Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_compose_weekly_digest_with_no_activity_has_no_content(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    content = await compose_weekly_digest(db_session, user=user)
    assert content.has_content is False


async def test_compose_weekly_digest_includes_score_deltas(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    today = datetime.now(UTC).date()
    db_session.add(
        GrowthScoreSnapshot(
            user_id=user.id,
            score_type="health",
            value=60.0,
            status="ok",
            scoring_version=1,
            snapshot_date=today.replace(day=max(1, today.day - 6)) if today.day > 6 else today,
        )
    )
    db_session.add(
        GrowthScoreSnapshot(
            user_id=user.id,
            score_type="health",
            value=72.0,
            status="ok",
            scoring_version=1,
            snapshot_date=today,
        )
    )
    await db_session.commit()

    content = await compose_weekly_digest(db_session, user=user)
    assert content.has_content is True
    assert len(content.score_deltas) == 1
    assert content.score_deltas[0].change == 12.0

    body = render_digest_body(content)
    assert "Health score is up 12 to 72" in body


async def test_compose_weekly_digest_includes_plan_items(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)
    db_session.add(
        Recommendation(
            audit_id=audit.id,
            user_id=user.id,
            category="profile",
            priority=1,
            title="Sharpen your headline",
            why="It's the first thing recruiters read.",
            action_label="Fix it",
            action_route="/profile",
            action_tool_id="profile.headline_optimizer",
            estimated_impact_points=8,
            status="open",
        )
    )
    await db_session.commit()

    await generate_plan_for_user(db_session, user=user)

    content = await compose_weekly_digest(db_session, user=user)
    assert content.has_content is True
    assert content.total_count > 0
    body = render_digest_body(content)
    assert "completed" in body.lower()
