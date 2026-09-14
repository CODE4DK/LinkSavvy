"""Persists a daily snapshot of each Growth Hub score so `/hubs/growth`
can show a real multi-month trend and a real before/after comparison,
rather than only ever showing "now". A score with no value (skipped or
insufficient_data) is never snapshotted -- there is nothing honest to
record, and recording a zero would fabricate a data point that isn't
there. At most one row per (user, score_type, day); see migration 0014.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.schema import GrowthScore
from app.models.growth_score_snapshot import GrowthScoreSnapshot
from app.models.profile_snapshot import ProfileSnapshotRow
from app.models.tool_run import ToolRun
from app.models.user import User

_SCORE_TYPES = ["health", "visibility", "consistency", "personal_branding"]


async def record_snapshots(db: AsyncSession, *, user: User, scores: dict[str, GrowthScore]) -> None:
    today = datetime.now(UTC).date()
    for score_type, score in scores.items():
        if score.value is None:
            continue
        exists = await db.execute(
            select(GrowthScoreSnapshot.id).where(
                GrowthScoreSnapshot.user_id == user.id,
                GrowthScoreSnapshot.score_type == score_type,
                GrowthScoreSnapshot.snapshot_date == today,
            )
        )
        if exists.scalar_one_or_none() is not None:
            continue
        db.add(
            GrowthScoreSnapshot(
                user_id=user.id,
                score_type=score_type,
                value=score.value,
                status=score.status.value,
                scoring_version=score.scoring_version,
                snapshot_date=today,
            )
        )
        try:
            await db.commit()
        except IntegrityError:
            # A concurrent request recorded today's snapshot first --
            # fine either way, no-op.
            await db.rollback()


async def get_score_history(
    db: AsyncSession, *, user_id: uuid.UUID, since: date
) -> dict[str, list[GrowthScoreSnapshot]]:
    result = await db.execute(
        select(GrowthScoreSnapshot)
        .where(
            GrowthScoreSnapshot.user_id == user_id,
            GrowthScoreSnapshot.snapshot_date >= since,
        )
        .order_by(GrowthScoreSnapshot.snapshot_date.asc())
    )
    by_type: dict[str, list[GrowthScoreSnapshot]] = {score_type: [] for score_type in _SCORE_TYPES}
    for row in result.scalars().all():
        by_type[row.score_type].append(row)
    return by_type


async def _nearest_snapshot_on_or_before(
    db: AsyncSession, *, user_id: uuid.UUID, score_type: str, day: date
) -> GrowthScoreSnapshot | None:
    result = await db.execute(
        select(GrowthScoreSnapshot)
        .where(
            GrowthScoreSnapshot.user_id == user_id,
            GrowthScoreSnapshot.score_type == score_type,
            GrowthScoreSnapshot.snapshot_date <= day,
        )
        .order_by(GrowthScoreSnapshot.snapshot_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_before_after(
    db: AsyncSession, *, user_id: uuid.UUID, from_date: date, to_date: date
) -> dict[str, Any]:
    """The Growth Hub's "proof of value" panel: which score components
    changed between two dates, and which tool runs and profile edits
    happened in between. Score deltas use the *nearest snapshot on or
    before* each date -- a snapshot only exists for a day the hub was
    actually visited, so this is the closest honest value rather than
    requiring an exact match. Component-level deltas aren't available
    (only each score's scalar value is snapshotted, not its per-component
    breakdown) -- a disclosed scope simplification, see ADR 0009."""
    score_deltas = []
    for score_type in _SCORE_TYPES:
        before = await _nearest_snapshot_on_or_before(
            db, user_id=user_id, score_type=score_type, day=from_date
        )
        after = await _nearest_snapshot_on_or_before(
            db, user_id=user_id, score_type=score_type, day=to_date
        )
        score_deltas.append(
            {
                "score_type": score_type,
                "from_value": before.value if before else None,
                "to_value": after.value if after else None,
                "delta": (after.value - before.value) if before and after else None,
            }
        )

    from_dt = datetime.combine(from_date, time.min, tzinfo=UTC)
    to_dt = datetime.combine(to_date, time.max, tzinfo=UTC)

    tool_runs_result = await db.execute(
        select(ToolRun)
        .where(
            ToolRun.user_id == user_id,
            ToolRun.created_at >= from_dt,
            ToolRun.created_at <= to_dt,
        )
        .order_by(ToolRun.created_at.asc())
    )
    tool_runs = [
        {"tool_id": run.tool_id, "status": run.status, "created_at": run.created_at}
        for run in tool_runs_result.scalars().all()
    ]

    profile_edits_result = await db.execute(
        select(ProfileSnapshotRow)
        .where(
            ProfileSnapshotRow.user_id == user_id,
            ProfileSnapshotRow.created_at >= from_dt,
            ProfileSnapshotRow.created_at <= to_dt,
        )
        .order_by(ProfileSnapshotRow.created_at.asc())
    )
    profile_edits = [
        {"version": row.version, "source": row.source, "created_at": row.created_at}
        for row in profile_edits_result.scalars().all()
    ]

    return {
        "from_date": from_date,
        "to_date": to_date,
        "score_deltas": score_deltas,
        "tool_runs": tool_runs,
        "profile_edits": profile_edits,
    }
