from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.schema import GrowthScoreStatus
from app.growth.scores.visibility import get_visibility_score
from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot
from tests.audit.categories.conftest import rich_snapshot


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-vis-{uuid.uuid4()}@example.com", full_name="Visibility Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_skipped_without_a_profile_snapshot(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    score = await get_visibility_score(db_session, user=user)
    assert score.status == GrowthScoreStatus.SKIPPED
    assert score.value is None
    assert score.needed is not None


async def test_scores_a_rich_profile(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    score = await get_visibility_score(db_session, user=user)

    assert score.value is not None
    by_name = {c.name: c for c in score.components}

    assert by_name["custom_url"].value == 100
    assert by_name["custom_url"].evidence == {"custom_url": "jamierivera"}

    assert by_name["profile_metadata"].value == 100
    assert by_name["profile_metadata"].evidence["industry_set"] is True

    assert by_name["recommendations_received"].value == 100
    assert by_name["recommendations_received"].evidence["recommendations_received"] == 6

    # rich_snapshot() has no profile_picture_url -- disclosed gap, not a
    # fabricated pass or fail.
    assert by_name["photo_and_banner"].value is None
    assert by_name["photo_and_banner"].evidence == {}

    assert by_name["skill_alignment"].value is not None
    assert by_name["skill_alignment"].evidence  # never empty when value is set

    assert by_name["keyword_coverage"].value is not None
    assert "backend" in by_name["keyword_coverage"].evidence["matched_keywords"]

    # At least one component is missing (photo_and_banner), so this can
    # never claim a clean "ok" for a profile with no photo.
    assert score.status == GrowthScoreStatus.PARTIAL
    for component in score.components:
        assert component.weight > 0
        if component.value is not None:
            assert component.evidence  # a score with no evidence is a bug
