from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.history import get_before_after
from app.models.growth_score_snapshot import GrowthScoreSnapshot
from app.models.profile_snapshot import ProfileSnapshotRow
from app.models.tool_run import ToolRun
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-ba-{uuid.uuid4()}@example.com", full_name="Before After Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _snapshot(db: AsyncSession, *, user: User, score_type: str, value: int, on: date) -> None:
    db.add(
        GrowthScoreSnapshot(
            user_id=user.id,
            score_type=score_type,
            value=value,
            status="ok",
            scoring_version="2026.1",
            snapshot_date=on,
        )
    )
    await db.commit()


async def test_score_deltas_use_the_nearest_snapshot_on_or_before_each_date(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    today = datetime.now(UTC).date()
    await _snapshot(
        db_session, user=user, score_type="visibility", value=40, on=today - timedelta(days=30)
    )
    await _snapshot(db_session, user=user, score_type="visibility", value=65, on=today)

    result = await get_before_after(
        db_session, user_id=user.id, from_date=today - timedelta(days=30), to_date=today
    )
    visibility = next(d for d in result["score_deltas"] if d["score_type"] == "visibility")
    assert visibility["from_value"] == 40
    assert visibility["to_value"] == 65
    assert visibility["delta"] == 25


async def test_score_delta_is_none_without_a_snapshot_on_either_side(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    today = datetime.now(UTC).date()

    result = await get_before_after(
        db_session, user_id=user.id, from_date=today - timedelta(days=30), to_date=today
    )
    for delta in result["score_deltas"]:
        assert delta["from_value"] is None
        assert delta["to_value"] is None
        assert delta["delta"] is None


async def test_tool_runs_and_profile_edits_in_the_window_are_included(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    today = datetime.now(UTC).date()
    from_date = today - timedelta(days=14)

    db_session.add(
        ToolRun(
            user_id=user.id,
            tool_id="profile.headline_optimizer",
            prompt_id="profile.headline_optimizer.v1",
            prompt_version=1,
            input={},
            output={"variants": []},
            context_keys=[],
            status="succeeded",
        )
    )
    db_session.add(
        ProfileSnapshotRow(
            user_id=user.id,
            version=1,
            source="manual",
            payload={},
            captured_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    result = await get_before_after(db_session, user_id=user.id, from_date=from_date, to_date=today)
    assert len(result["tool_runs"]) == 1
    assert result["tool_runs"][0]["tool_id"] == "profile.headline_optimizer"
    assert len(result["profile_edits"]) == 1
    assert result["profile_edits"][0]["version"] == 1


async def test_excludes_activity_outside_the_window(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    today = datetime.now(UTC).date()

    db_session.add(
        ToolRun(
            user_id=user.id,
            tool_id="profile.headline_optimizer",
            prompt_id="profile.headline_optimizer.v1",
            prompt_version=1,
            input={},
            output={"variants": []},
            context_keys=[],
            status="succeeded",
        )
    )
    await db_session.commit()

    result = await get_before_after(
        db_session,
        user_id=user.id,
        from_date=today - timedelta(days=60),
        to_date=today - timedelta(days=30),
    )
    assert result["tool_runs"] == []
