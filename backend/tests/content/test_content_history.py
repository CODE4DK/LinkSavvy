from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.content.content_history import resolve_content_history
from app.models.content_plan import ContentPlan
from app.models.content_sample import ContentSample
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"history-{uuid.uuid4()}@example.com", full_name="History Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_returns_the_explicit_history_when_supplied(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    result = await resolve_content_history(
        db_session, user_id=user.id, explicit=["a supplied post"]
    )
    assert result == ["a supplied post"]


async def test_returns_none_when_the_user_has_no_history_anywhere(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    result = await resolve_content_history(db_session, user_id=user.id, explicit=None)
    assert result is None


async def test_falls_back_to_posted_content_plans(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    db_session.add(
        ContentPlan(
            user_id=user.id,
            body_preview="A post I actually published",
            status="posted",
            planned_for=date(2026, 6, 1),
        )
    )
    db_session.add(
        ContentPlan(
            user_id=user.id,
            body_preview="Just an idea, never posted",
            status="idea",
            planned_for=date(2026, 6, 1),
        )
    )
    await db_session.commit()

    result = await resolve_content_history(db_session, user_id=user.id, explicit=None)
    assert result == ["A post I actually published"]


async def test_falls_back_to_content_samples(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    db_session.add(ContentSample(user_id=user.id, body="A sample post", source="paste"))
    await db_session.commit()

    result = await resolve_content_history(db_session, user_id=user.id, explicit=None)
    assert result == ["A sample post"]


async def test_ignores_soft_deleted_rows(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    db_session.add(
        ContentPlan(
            user_id=user.id,
            body_preview="Deleted post",
            status="posted",
            planned_for=date(2026, 6, 1),
            deleted_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    result = await resolve_content_history(db_session, user_id=user.id, explicit=None)
    assert result is None
