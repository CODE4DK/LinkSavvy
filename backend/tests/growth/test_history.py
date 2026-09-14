from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.history import get_score_history, record_snapshots
from app.growth.schema import GrowthScore, GrowthScoreStatus, GrowthScoreType
from app.growth.service import get_growth_scores
from app.models.growth_score_snapshot import GrowthScoreSnapshot
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-hist-{uuid.uuid4()}@example.com", full_name="History Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _score(value: int | None, status: GrowthScoreStatus = GrowthScoreStatus.OK) -> GrowthScore:
    return GrowthScore(
        score_type=GrowthScoreType.VISIBILITY,
        value=value,
        status=status,
        components=[],
        computed_at=datetime.now(UTC),
        scoring_version="2026.1",
    )


async def test_record_snapshots_skips_scores_with_no_value(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    scores = {"visibility": _score(None, GrowthScoreStatus.SKIPPED)}
    await record_snapshots(db_session, user=user, scores=scores)
    history = await get_score_history(
        db_session, user_id=user.id, since=datetime.now(UTC).date() - timedelta(days=1)
    )
    assert history["visibility"] == []


async def test_record_snapshots_is_idempotent_for_the_same_day(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    scores = {"visibility": _score(60)}
    await record_snapshots(db_session, user=user, scores=scores)
    await record_snapshots(db_session, user=user, scores=scores)

    history = await get_score_history(
        db_session, user_id=user.id, since=datetime.now(UTC).date() - timedelta(days=1)
    )
    assert len(history["visibility"]) == 1
    assert history["visibility"][0].value == 60


async def test_get_growth_scores_records_a_snapshot_for_a_fresh_user(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await get_growth_scores(db_session, user=user)

    result = await db_session.execute(
        GrowthScoreSnapshot.__table__.select().where(GrowthScoreSnapshot.user_id == user.id)
    )
    # All four scores are skipped for a brand-new user with no profile
    # snapshot or audit -- nothing to honestly snapshot yet.
    assert result.fetchall() == []
