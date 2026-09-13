from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.growth.schema import GrowthScoreStatus
from app.growth.scores.personal_branding import get_personal_branding_score
from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot
from tests.audit.categories.conftest import rich_snapshot


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-brand-{uuid.uuid4()}@example.com", full_name="Branding Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _fake_gateway_result(parsed: dict[str, Any]) -> gateway.GatewayResult:
    return gateway.GatewayResult(
        text=None,
        parsed=parsed,
        model="fake-model",
        provider="fake",
        tokens_in=1,
        tokens_out=1,
        cost_minor=0,
        currency="usd",
        latency_ms=0.0,
        cached=False,
        fallback_used=False,
        correlation_id="corr-1",
        invocation_id=uuid.uuid4(),
    )


async def test_skipped_without_a_profile_snapshot(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    score = await get_personal_branding_score(db_session, user=user)
    assert score.status == GrowthScoreStatus.SKIPPED
    assert score.value is None
    assert score.needed is not None


async def test_scores_a_rich_profile_via_the_real_fixture(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    score = await get_personal_branding_score(db_session, user=user)

    assert score.value is not None
    assert score.status == GrowthScoreStatus.OK
    assert len(score.components) == 5
    for component in score.components:
        assert component.weight > 0
        assert component.value is not None
        assert component.evidence  # a score with no evidence is a bug


async def test_drops_a_component_with_blank_evidence(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    async def _fake_run(*args: Any, **kwargs: Any) -> gateway.GatewayResult:
        return _fake_gateway_result(
            {
                "components": [
                    {"code": "positioning_clarity", "score": 80, "evidence": "Clear headline."},
                    {"code": "message_consistency", "score": 70, "evidence": "Consistent story."},
                    {"code": "distinctiveness", "score": 0, "evidence": "   "},
                    {"code": "proof", "score": 0, "evidence": ""},
                    {
                        "code": "content_profile_alignment",
                        "score": 60,
                        "evidence": "Content matches profile themes.",
                    },
                ]
            }
        )

    monkeypatch.setattr(gateway, "run", _fake_run)

    score = await get_personal_branding_score(db_session, user=user)

    assert score.status == GrowthScoreStatus.PARTIAL
    by_name = {c.name: c for c in score.components}
    assert len(score.components) == 3
    assert "Distinctiveness" not in by_name
    assert "Proof" not in by_name
    assert by_name["Positioning clarity"].value == 80


async def test_skipped_when_every_component_lacks_evidence(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    async def _fake_run(*args: Any, **kwargs: Any) -> gateway.GatewayResult:
        return _fake_gateway_result(
            {
                "components": [
                    {"code": "positioning_clarity", "score": 80, "evidence": ""},
                    {"code": "message_consistency", "score": 70, "evidence": "  "},
                ]
            }
        )

    monkeypatch.setattr(gateway, "run", _fake_run)

    score = await get_personal_branding_score(db_session, user=user)

    assert score.status == GrowthScoreStatus.SKIPPED
    assert score.value is None
    assert score.components == []
    assert score.needed is not None
