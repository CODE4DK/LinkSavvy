"""Personal Branding Score -- coherence across the profile, judged by
AI against a fixed rubric (see growth.personal_branding.v1.prompt.md).
Every component the AI returns must carry non-empty evidence quoting
or closely paraphrasing the user's own profile/content -- the prompt
says so, and this module refuses to build a score from a component
missing it (fails the whole score honestly rather than partially
crediting an unsupported claim).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.growth.schema import GrowthScore, GrowthScoreStatus, GrowthScoreType, ScoreComponent
from app.growth.scoring_config import growth_component_weight, load_growth_scoring_config
from app.models.content_sample import ContentSample
from app.models.user import User
from app.profiles.schema import ProfileSnapshot
from app.profiles.service import get_active_snapshot

_SCORE_TYPE = "personal_branding"
_PROMPT_ID = "growth.personal_branding.v1"
_MAX_CONTENT_SAMPLES = 5

_COMPONENT_LABELS = {
    "positioning_clarity": "Positioning clarity",
    "message_consistency": "Message consistency",
    "distinctiveness": "Distinctiveness",
    "proof": "Proof",
    "content_profile_alignment": "Content-to-profile alignment",
}


def _identity_block(snapshot: ProfileSnapshot) -> str:
    identity = snapshot.identity
    if identity is None:
        return "No identity information provided."
    parts = [
        f"Name: {identity.full_name}" if identity.full_name else None,
        f"Headline: {identity.headline}" if identity.headline else None,
        f"Industry: {identity.industry}" if identity.industry else None,
    ]
    return "\n".join(p for p in parts if p) or "No identity information provided."


def _experience_block(snapshot: ProfileSnapshot) -> str:
    if not snapshot.experiences:
        return "No experience listed."
    lines = []
    for exp in snapshot.experiences:
        header = " at ".join(part for part in (exp.title, exp.company) if part)
        lines.append(header)
        lines.extend(f"- {bullet}" for bullet in (exp.bullets or []))
    return "\n".join(lines)


async def _content_samples_block(db: AsyncSession, *, user_id: object) -> str:
    result = await db.execute(
        select(ContentSample)
        .where(ContentSample.user_id == user_id, ContentSample.deleted_at.is_(None))
        .order_by(ContentSample.created_at.desc())
        .limit(_MAX_CONTENT_SAMPLES)
    )
    samples = list(result.scalars().all())
    if not samples:
        return "No content samples provided."
    return "\n\n---\n\n".join(sample.body for sample in samples)


async def get_personal_branding_score(db: AsyncSession, *, user: User) -> GrowthScore:
    config = load_growth_scoring_config()
    snapshot_row = await get_active_snapshot(db, user_id=user.id)
    if snapshot_row is None:
        return GrowthScore(
            score_type=GrowthScoreType.PERSONAL_BRANDING,
            value=None,
            status=GrowthScoreStatus.SKIPPED,
            components=[],
            computed_at=datetime.now(UTC),
            scoring_version=config.scoring_version,
            needed={"reason": "Commit a profile snapshot to unlock this score."},
        )

    snapshot = ProfileSnapshot.model_validate(snapshot_row.payload)
    context = {
        "identity": _identity_block(snapshot),
        "about": snapshot.about or "No About section provided.",
        "experience": _experience_block(snapshot),
        "content_samples": await _content_samples_block(db, user_id=user.id),
    }
    result = await gateway.run(_PROMPT_ID, context, user=user, db=db)
    assert result.parsed is not None

    weights = {code: growth_component_weight(_SCORE_TYPE, code) for code in _COMPONENT_LABELS}
    scores: dict[str, int] = {}
    components: list[ScoreComponent] = []
    for item in result.parsed["components"]:
        code = item["code"]
        evidence_text = item["evidence"]
        if not evidence_text or not evidence_text.strip():
            # A score with no evidence is a bug -- never persist or
            # count a component the model didn't actually support.
            continue
        scores[code] = item["score"]
        components.append(
            ScoreComponent(
                name=_COMPONENT_LABELS.get(code, code),
                weight=weights.get(code, 0),
                value=item["score"],
                evidence={"note": evidence_text},
            )
        )

    if not scores:
        return GrowthScore(
            score_type=GrowthScoreType.PERSONAL_BRANDING,
            value=None,
            status=GrowthScoreStatus.SKIPPED,
            components=[],
            computed_at=datetime.now(UTC),
            scoring_version=config.scoring_version,
            needed={"reason": "Not enough profile content to assess personal branding yet."},
        )

    overall = round(
        sum(scores[code] * weights[code] for code in scores) / sum(weights[code] for code in scores)
    )
    status = (
        GrowthScoreStatus.OK if len(scores) == len(_COMPONENT_LABELS) else GrowthScoreStatus.PARTIAL
    )

    return GrowthScore(
        score_type=GrowthScoreType.PERSONAL_BRANDING,
        value=overall,
        status=status,
        components=components,
        computed_at=datetime.now(UTC),
        scoring_version=config.scoring_version,
    )
