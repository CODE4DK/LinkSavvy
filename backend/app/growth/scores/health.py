"""Health Score -- not a new computation. Phase 4's Audit Engine
already computes this as the overall audit score; this module only
reshapes the most recent `ScoreHistory` row into the common
`GrowthScore` envelope, with the five audit categories as its
components (each category's own weight from config/scoring.yaml).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.scoring import load_scoring_config
from app.growth.schema import GrowthScore, GrowthScoreStatus, GrowthScoreType, ScoreComponent
from app.models.score_history import ScoreHistory

_CATEGORY_LABELS = {
    "profile": "Profile",
    "content": "Content",
    "engagement": "Engagement",
    "career": "Career",
    "visibility": "Visibility",
}


async def get_health_score(db: AsyncSession, *, user_id: uuid.UUID) -> GrowthScore:
    latest = (
        await db.execute(
            select(ScoreHistory)
            .where(ScoreHistory.user_id == user_id)
            .order_by(ScoreHistory.recorded_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if latest is None:
        return GrowthScore(
            score_type=GrowthScoreType.HEALTH,
            value=None,
            status=GrowthScoreStatus.SKIPPED,
            components=[],
            computed_at=datetime.now(UTC),
            scoring_version=load_scoring_config().scoring_version,
            needed={"reason": "Run your first audit from the Dashboard to unlock this score."},
        )

    weights = load_scoring_config().category_weights
    components: list[ScoreComponent] = []
    any_missing = False
    for code, label in _CATEGORY_LABELS.items():
        value = getattr(latest, code)
        if value is None:
            any_missing = True
        components.append(
            ScoreComponent(
                name=label,
                weight=weights[code],
                value=value,
                evidence=(
                    {
                        "audit_id": str(latest.audit_id),
                        "recorded_at": latest.recorded_at.isoformat(),
                    }
                    if value is not None
                    else {}
                ),
            )
        )

    return GrowthScore(
        score_type=GrowthScoreType.HEALTH,
        value=latest.overall,
        status=GrowthScoreStatus.PARTIAL if any_missing else GrowthScoreStatus.OK,
        components=components,
        computed_at=latest.recorded_at,
        scoring_version=latest.scoring_version,
    )
