from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.categories import career
from app.models.user import User

from .conftest import (
    SAMPLE_ROLE_KEYWORDS,
    empty_snapshot,
    make_context,
    partial_skills_snapshot,
    rich_snapshot,
)


async def test_career_skipped_with_no_target_role(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(user=audit_user, db=db_session, snapshot=empty_snapshot(), target_role=None)
    result = await career.run(ctx)
    assert result.status == "skipped"
    assert result.score is None
    codes = [f.code for f in result.findings]
    assert "career.no_target_role" in codes
    assert "career.no_resume_uploaded" in codes  # always present -- no ingestion path yet


async def test_career_skipped_when_role_keywords_unavailable(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(user=audit_user, db=db_session, snapshot=rich_snapshot(), role_keywords=None)
    result = await career.run(ctx)
    assert result.status == "skipped"
    assert result.score is None
    assert "career.no_role_keywords" in [f.code for f in result.findings]


async def test_career_skipped_when_skills_unlisted(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(
        user=audit_user,
        db=db_session,
        snapshot=empty_snapshot(),
        role_keywords=SAMPLE_ROLE_KEYWORDS,
    )
    result = await career.run(ctx)
    assert result.status == "skipped"
    assert "career.no_skills_listed" in [f.code for f in result.findings]


async def test_career_partial_with_full_skill_overlap(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(
        user=audit_user,
        db=db_session,
        snapshot=rich_snapshot(),
        role_keywords=SAMPLE_ROLE_KEYWORDS,
    )
    result = await career.run(ctx)
    assert result.status == "partial"  # resume_presence never available
    assert result.score == 100
    assert result.detail["matched_skills"] == SAMPLE_ROLE_KEYWORDS.must_have_skills
    codes = [f.code for f in result.findings]
    assert "career.missing_target_role_skills" not in codes


async def test_career_flags_missing_skills_for_target_role(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(
        user=audit_user,
        db=db_session,
        snapshot=partial_skills_snapshot(),
        role_keywords=SAMPLE_ROLE_KEYWORDS,
    )
    result = await career.run(ctx)
    assert result.score == 40
    finding = next(f for f in result.findings if f.code == "career.missing_target_role_skills")
    assert finding.severity == "important"  # 3 of 5 missing -> majority
    assert finding.evidence["missing_skills"] == ["Distributed Systems", "API Design", "Kubernetes"]
