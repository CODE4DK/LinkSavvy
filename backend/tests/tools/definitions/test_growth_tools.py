"""Golden tests for Growth Hub tools -- currently just Networking
Recommendations. See tests/tools/definitions/test_profile_tools.py for
the shared `output_of`/`assert_never_fabricates` helpers and
test_engagement_tools.py for the refusal-rule test pattern this mirrors.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.loader import get_prompt
from app.models.user import User
from app.tools import service

from .test_profile_tools import assert_never_fabricates, output_of

_EXPECTED_HEADINGS = [
    "People to build relationships with",
    "Communities and conversations worth joining",
    "A realistic weekly cadence",
    "Warm-intro paths through your existing network",
]


async def test_networking_recommendations_golden(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    run, quota, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="growth.networking_recommendations",
        raw_input={"industry": "software", "content_themes": "backend reliability, on-call"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert len(output["sections"]) == 4
    assert [s["heading"] for s in output["sections"]] == _EXPECTED_HEADINGS
    for section in output["sections"]:
        assert section["heading"]
        assert section["body"] or section["bullets"]
    assert_never_fabricates(output)
    assert quota.metric == "tool_runs"


def _output_text(output: dict[str, object]) -> str:
    import json

    return json.dumps(output).lower()


async def test_networking_recommendations_never_produces_named_individuals_or_lead_lists(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="growth.networking_recommendations",
        raw_input={"industry": "software", "content_themes": "backend reliability"},
    )
    text = _output_text(output_of(run))
    for banned in ("lead list", "scraped", "purchased contact", "bulk outreach", "mass outreach"):
        assert banned not in text


def test_networking_recommendations_prompt_carries_the_refusal_rule() -> None:
    body = get_prompt("growth.networking_recommendations.v1").body.lower()
    assert "lead list" in body
    assert "scraped or purchased" in body
    assert "bulk/mass outreach" in body
    assert "never named individuals" in body or "never inventing a specific person" in body
