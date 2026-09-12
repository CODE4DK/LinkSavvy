from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.categories import profile
from app.audit.context import AuditContext
from app.models.user import User
from app.profiles.schema import ProfileSnapshot

from .conftest import SAMPLE_ROLE_KEYWORDS, make_context, rich_snapshot


def _ctx(
    user: User,
    db: AsyncSession,
    *,
    snapshot: ProfileSnapshot | None = None,
    target_role: str | None = "Staff Backend Engineer",
    role_keywords: object = SAMPLE_ROLE_KEYWORDS,
) -> AuditContext:
    return make_context(
        user=user,
        db=db,
        snapshot=snapshot or rich_snapshot(),
        target_role=target_role,
        role_keywords=role_keywords,  # type: ignore[arg-type]
    )


async def test_profile_ok_with_full_skill_overlap(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = _ctx(audit_user, db_session)
    result = await profile.run(ctx)

    assert result.status == "ok"
    assert result.score == 54
    assert result.detail["quality"]["headline"]["score"] == 45
    assert result.detail["quality"]["about"]["score"] == 30
    assert result.detail["quality"]["experience"]["score"] == 55

    codes = [f.code for f in result.findings]
    # 4 completeness gaps for rich_snapshot (see conftest) + 2+3+2 AI quality issues
    assert codes.count("profile.completeness.has_minimum_experiences") == 1
    assert codes.count("profile.completeness.has_minimum_skills") == 1
    assert codes.count("profile.completeness.has_certification_or_project") == 1
    assert codes.count("profile.completeness.has_profile_photo") == 1
    assert codes.count("profile.headline_quality_issue") == 2
    assert codes.count("profile.about_quality_issue") == 3
    assert codes.count("profile.experience_quality_issue") == 2
    assert "profile.no_skills_coverage_context" not in codes


async def test_profile_completeness_gap_severities_are_mapped(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = _ctx(audit_user, db_session)
    result = await profile.run(ctx)
    by_code = {f.code: f for f in result.findings}
    # has_minimum_experiences is "high" in completeness_rules.yaml -> "critical"
    assert by_code["profile.completeness.has_minimum_experiences"].severity == "critical"
    # has_minimum_skills is "medium" -> "important"
    assert by_code["profile.completeness.has_minimum_skills"].severity == "important"
    # has_profile_photo is "low" -> "opportunity"
    assert by_code["profile.completeness.has_profile_photo"].severity == "opportunity"


async def test_profile_partial_without_target_role(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = _ctx(audit_user, db_session, target_role=None, role_keywords=None)
    result = await profile.run(ctx)
    assert result.status == "partial"
    assert result.score == 45
    assert "profile.no_skills_coverage_context" in [f.code for f in result.findings]
