from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.schema import GrowthScoreStatus
from app.growth.scores.health import get_health_score
from app.models.audit import Audit
from app.models.score_history import ScoreHistory
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"health-{uuid.uuid4()}@example.com", full_name="Health Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_skipped_when_no_audit_has_ever_run(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    score = await get_health_score(db_session, user_id=user.id)
    assert score.status == GrowthScoreStatus.SKIPPED
    assert score.value is None
    assert score.components == []
    assert score.needed is not None


async def test_reshapes_the_latest_score_history_row(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    db_session.add(
        ScoreHistory(
            user_id=user.id,
            audit_id=audit.id,
            scoring_version="2026.1",
            overall=72,
            profile=80,
            content=None,
            engagement=60,
            career=None,
            visibility=70,
            recorded_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    score = await get_health_score(db_session, user_id=user.id)
    assert score.value == 72
    assert score.status == GrowthScoreStatus.PARTIAL  # content/career missing
    by_name = {c.name: c for c in score.components}
    assert by_name["Profile"].value == 80
    assert by_name["Profile"].evidence  # never empty when value is set
    assert by_name["Content"].value is None
    assert by_name["Content"].evidence == {}
    assert len(score.components) == 5


async def test_uses_the_most_recent_row_when_several_exist(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    older = ScoreHistory(
        user_id=user.id,
        audit_id=audit.id,
        scoring_version="2026.1",
        overall=50,
        profile=50,
        content=50,
        engagement=50,
        career=50,
        visibility=50,
        recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    newer = ScoreHistory(
        user_id=user.id,
        audit_id=audit.id,
        scoring_version="2026.1",
        overall=90,
        profile=90,
        content=90,
        engagement=90,
        career=90,
        visibility=90,
        recorded_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    db_session.add_all([older, newer])
    await db_session.commit()

    score = await get_health_score(db_session, user_id=user.id)
    assert score.value == 90
    assert score.status == GrowthScoreStatus.OK
