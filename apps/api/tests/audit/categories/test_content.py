from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.categories import content
from app.models.user import User

from .conftest import empty_snapshot, make_context, rich_snapshot


async def test_content_skipped_with_no_history_and_no_skills(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(user=audit_user, db=db_session, snapshot=empty_snapshot())
    result = await content.run(ctx)
    assert result.status == "skipped"
    assert result.score is None
    assert "unlock" in result.inputs_available


async def test_content_partial_with_skills_but_no_history(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(user=audit_user, db=db_session, snapshot=rich_snapshot())
    result = await content.run(ctx)
    assert result.status == "partial"
    assert result.score == 100  # 5 skills -> min(100, 5*20)
    codes = [f.code for f in result.findings]
    assert "content.no_history_supplied" in codes
    assert "content.opportunity_from_skills" in codes


async def test_content_ok_with_history_and_skills(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(
        user=audit_user,
        db=db_session,
        snapshot=rich_snapshot(),
        content_history=["Post one", "Post two", "Post three"],
    )
    result = await content.run(ctx)
    assert result.status == "ok"
    assert result.score == 58  # weighted_average(posting=30, opportunities=100; 60/40)
    codes = [f.code for f in result.findings]
    assert "content.no_history_supplied" not in codes


async def test_content_skipped_when_skills_are_confirmed_empty(
    audit_user: User, db_session: AsyncSession
) -> None:
    """`skills=[]` means "confirmed none", not "unknown" -- content should
    still skip rather than guess an opportunity out of nothing."""
    snapshot = empty_snapshot().model_copy(update={"skills": []})
    ctx = make_context(user=audit_user, db=db_session, snapshot=snapshot)
    result = await content.run(ctx)
    assert result.status == "skipped"
    assert result.score is None
