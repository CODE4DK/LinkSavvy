from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.categories import engagement
from app.models.user import User

from .conftest import empty_snapshot, make_context, rich_snapshot


async def test_engagement_skipped_with_nothing_known(
    audit_user: User, db_session: AsyncSession
) -> None:
    ctx = make_context(user=audit_user, db=db_session, snapshot=empty_snapshot(), target_role=None)
    result = await engagement.run(ctx)
    assert result.status == "skipped"
    assert result.score is None
    codes = [f.code for f in result.findings]
    assert "engagement.no_network_metrics" in codes
    assert "engagement.no_contactability_signals" in codes
    assert "engagement.no_opportunities_context" in codes


async def test_engagement_ok_with_rich_profile(audit_user: User, db_session: AsyncSession) -> None:
    ctx = make_context(user=audit_user, db=db_session, snapshot=rich_snapshot())
    result = await engagement.run(ctx)
    assert result.status == "ok"
    assert result.score == 94
    assert result.detail["network_sub_scores"] == {
        "connections": 100,
        "followers": 40,
        "recommendations": 100,
    }
    assert result.detail["contact_sub_scores"] == {"custom_url": 100, "contact_cta": 100}
    assert len(result.detail["opportunities"]) == 3
    codes = [f.code for f in result.findings]
    assert codes.count("engagement.opportunity_suggested") == 3


async def test_engagement_partial_renormalizes_when_metrics_and_role_are_missing(
    audit_user: User, db_session: AsyncSession
) -> None:
    snapshot = rich_snapshot().model_copy(update={"metrics": None})
    ctx = make_context(user=audit_user, db=db_session, snapshot=snapshot, target_role=None)
    result = await engagement.run(ctx)
    assert result.status == "partial"
    assert result.score == 100  # only contactability (30/30 weight) is available
    codes = [f.code for f in result.findings]
    assert "engagement.no_network_metrics" in codes
    assert "engagement.no_opportunities_context" in codes
    assert "engagement.no_contactability_signals" not in codes


async def test_engagement_flags_confirmed_absent_url_and_cta(
    audit_user: User, db_session: AsyncSession
) -> None:
    """`custom_url=""` and an About with no CTA are *known* facts, not
    unknowns -- these should score low and raise findings, not skip."""
    snapshot = rich_snapshot().model_copy(
        update={"about": "Just a short bio with no way to reach me."}
    )
    assert snapshot.identity is not None
    identity = snapshot.identity.model_copy(update={"custom_url": ""})
    snapshot = snapshot.model_copy(update={"identity": identity})
    ctx = make_context(user=audit_user, db=db_session, snapshot=snapshot)
    result = await engagement.run(ctx)
    codes = [f.code for f in result.findings]
    assert "engagement.no_custom_url" in codes
    assert "engagement.no_contact_cta" in codes
