from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.categories import visibility
from app.models.user import User

from .conftest import SAMPLE_ROLE_KEYWORDS, empty_snapshot, make_context, rich_snapshot


async def test_visibility_skipped_with_nothing_known(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(user=audit_user, db=db_session, snapshot=empty_snapshot(), target_role=None)
    result = await visibility.run(ctx)
    assert result.status == "skipped"
    assert result.score is None


async def test_visibility_ok_with_rich_profile_and_role_keywords(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(
        user=audit_user,
        db=db_session,
        snapshot=rich_snapshot(),
        role_keywords=SAMPLE_ROLE_KEYWORDS,
    )
    result = await visibility.run(ctx)
    assert result.status == "ok"
    assert result.score == 76
    assert result.detail["matched_keywords"] == ["distributed systems"]
    assert not any(f.code == "visibility.inconsistent_brand_vocabulary" for f in result.findings)


async def test_visibility_partial_without_role_keywords(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(
        user=audit_user,
        db=db_session,
        snapshot=rich_snapshot(),
        target_role=None,
        role_keywords=None,
    )
    result = await visibility.run(ctx)
    assert result.status == "partial"
    assert result.score == 100  # only custom_url + profile_metadata contribute
    codes = [f.code for f in result.findings]
    assert "visibility.no_target_role_for_keywords" in codes


async def test_visibility_flags_missing_metadata(
    audit_user: User, db_session: AsyncSession
) -> None:
    snapshot = rich_snapshot()
    assert snapshot.identity is not None
    identity = snapshot.identity.model_copy(update={"industry": "", "location": ""})
    snapshot = snapshot.model_copy(update={"identity": identity})
    ctx = make_context(
        user=audit_user, db=db_session, snapshot=snapshot, role_keywords=SAMPLE_ROLE_KEYWORDS
    )
    result = await visibility.run(ctx)
    codes = [f.code for f in result.findings]
    assert "visibility.no_industry" in codes
    assert "visibility.no_location" in codes
