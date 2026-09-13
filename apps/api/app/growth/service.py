"""Runs the four Growth Hub scores together for `/hubs/growth`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.history import record_snapshots
from app.growth.schema import GrowthScore
from app.growth.scores.consistency import get_consistency_score
from app.growth.scores.health import get_health_score
from app.growth.scores.personal_branding import get_personal_branding_score
from app.growth.scores.visibility import get_visibility_score
from app.models.user import User


async def get_growth_scores(db: AsyncSession, *, user: User) -> dict[str, GrowthScore]:
    # Sequential, not gathered: these all share the one `db` session, and
    # AsyncSession isn't safe to drive from more than one coroutine at a
    # time (see app/jobs/registry.py's own note on this).
    scores = {
        "health": await get_health_score(db, user_id=user.id),
        "visibility": await get_visibility_score(db, user=user),
        "consistency": await get_consistency_score(db, user=user),
        "personal_branding": await get_personal_branding_score(db, user=user),
    }
    await record_snapshots(db, user=user, scores=scores)
    return scores
