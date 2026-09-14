"""Visibility Score -- keyword coverage, discoverability metadata, and
social proof that make a profile easier to find and to trust once
found. Deterministic apart from the keyword-relevance judgement, which
reuses `app.audit.role_keywords.get_role_keywords` (the same AI call
Phase 4's audit engine makes, cached by the gateway on
`(prompt, target_role)`, so scoring visibility repeatedly costs no
extra AI calls beyond the first for a given target role).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.role_keywords import get_role_keywords
from app.audit.scoring import weighted_average
from app.audit.target_role import resolve_target_role
from app.growth.schema import GrowthScore, GrowthScoreStatus, GrowthScoreType, ScoreComponent
from app.growth.scoring_config import growth_component_weight, load_growth_scoring_config
from app.models.user import User
from app.profiles.schema import ProfileSnapshot
from app.profiles.service import get_active_snapshot

_SCORE_TYPE = "visibility"
_RECOMMENDATIONS_TARGET = 3


def _contains(text: str, keyword: str) -> bool:
    return re.search(re.escape(keyword), text, re.IGNORECASE) is not None


def _keyword_coverage(
    snapshot: ProfileSnapshot, keywords: list[str]
) -> tuple[int | None, dict[str, object]]:
    if not keywords:
        return None, {}
    headline = (snapshot.identity.headline if snapshot.identity else None) or ""
    about = snapshot.about or ""
    experience_text = "\n".join(
        " ".join([exp.description or "", *(exp.bullets or [])])
        for exp in (snapshot.experiences or [])
    )
    combined = "\n".join([headline, about, experience_text])
    present = [kw for kw in keywords if _contains(combined, kw)]
    value = round(100 * len(present) / len(keywords))
    return value, {"matched_keywords": present, "of_total": len(keywords)}


def _custom_url(snapshot: ProfileSnapshot) -> tuple[int | None, dict[str, object]]:
    identity = snapshot.identity
    if identity is None or identity.custom_url is None:
        return None, {}
    value = 100 if identity.custom_url else 0
    return value, {"custom_url": identity.custom_url}


def _profile_metadata(snapshot: ProfileSnapshot) -> tuple[int | None, dict[str, object]]:
    identity = snapshot.identity
    if identity is None:
        return None, {}
    sub_scores = []
    evidence: dict[str, object] = {}
    if identity.industry is not None:
        sub_scores.append(100 if identity.industry else 0)
        evidence["industry_set"] = bool(identity.industry)
    if identity.location is not None:
        sub_scores.append(100 if identity.location else 0)
        evidence["location_set"] = bool(identity.location)
    if not sub_scores:
        return None, {}
    return round(sum(sub_scores) / len(sub_scores)), evidence


def _skill_alignment(
    snapshot: ProfileSnapshot, must_have_skills: list[str]
) -> tuple[int | None, dict[str, object]]:
    if not must_have_skills or snapshot.skills is None:
        return None, {}
    user_skills = {skill.name.strip().lower() for skill in snapshot.skills if skill.name}
    matched = [s for s in must_have_skills if s.strip().lower() in user_skills]
    value = round(100 * len(matched) / len(must_have_skills))
    return value, {"matched_skills": matched, "of_total": len(must_have_skills)}


def _photo_and_banner(snapshot: ProfileSnapshot) -> tuple[int | None, dict[str, object]]:
    identity = snapshot.identity
    if identity is None or identity.profile_picture_url is None:
        return None, {}
    # ProfileSnapshot doesn't capture a banner image anywhere yet (see
    # docs/adr/0009) -- this component is honestly photo-only until a
    # later phase adds banner capture, not silently scored as if it
    # checked both.
    has_photo = bool(identity.profile_picture_url)
    return (100 if has_photo else 0), {
        "has_photo": has_photo,
        "banner_checked": False,
    }


def _recommendations_received(snapshot: ProfileSnapshot) -> tuple[int | None, dict[str, object]]:
    if snapshot.metrics is None or snapshot.metrics.recommendations_received is None:
        return None, {}
    count = snapshot.metrics.recommendations_received
    value = min(100, round(100 * count / _RECOMMENDATIONS_TARGET))
    return value, {"recommendations_received": count}


async def get_visibility_score(db: AsyncSession, *, user: User) -> GrowthScore:
    config = load_growth_scoring_config()
    snapshot_row = await get_active_snapshot(db, user_id=user.id)
    if snapshot_row is None:
        return GrowthScore(
            score_type=GrowthScoreType.VISIBILITY,
            value=None,
            status=GrowthScoreStatus.SKIPPED,
            components=[],
            computed_at=datetime.now(UTC),
            scoring_version=config.scoring_version,
            needed={"reason": "Commit a profile snapshot to unlock this score."},
        )

    snapshot = ProfileSnapshot.model_validate(snapshot_row.payload)
    target_role, _ = resolve_target_role(snapshot, supplied=None)
    role_keywords = await get_role_keywords(target_role=target_role, user=user, db=db)
    keywords = role_keywords.keywords if role_keywords else []
    must_have_skills = role_keywords.must_have_skills if role_keywords else []

    raw: dict[str, tuple[int | None, dict[str, object]]] = {
        "keyword_coverage": _keyword_coverage(snapshot, keywords),
        "custom_url": _custom_url(snapshot),
        "profile_metadata": _profile_metadata(snapshot),
        "skill_alignment": _skill_alignment(snapshot, must_have_skills),
        "photo_and_banner": _photo_and_banner(snapshot),
        "recommendations_received": _recommendations_received(snapshot),
    }

    scores = {code: value for code, (value, _evidence) in raw.items()}
    weights = {code: growth_component_weight(_SCORE_TYPE, code) for code in raw}
    overall = weighted_average(scores, weights)

    components = [
        ScoreComponent(
            name=code,
            weight=weights[code],
            value=value,
            evidence=evidence,
        )
        for code, (value, evidence) in raw.items()
    ]

    if overall is None:
        return GrowthScore(
            score_type=GrowthScoreType.VISIBILITY,
            value=None,
            status=GrowthScoreStatus.SKIPPED,
            components=components,
            computed_at=datetime.now(UTC),
            scoring_version=config.scoring_version,
            needed={"reason": "Fill in more of your profile to unlock this score."},
        )

    status = (
        GrowthScoreStatus.OK
        if all(value is not None for value, _ in raw.values())
        else GrowthScoreStatus.PARTIAL
    )
    return GrowthScore(
        score_type=GrowthScoreType.VISIBILITY,
        value=overall,
        status=status,
        components=components,
        computed_at=datetime.now(UTC),
        scoring_version=config.scoring_version,
    )
