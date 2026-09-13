"""Golden tests for the seven Profile Hub tools: each runs for real
through `app/tools/service.py` against the real tool/prompt registries,
with only the AI provider faked (see `tests/conftest.py`'s autouse
`_fake_ai_providers`). Every assertion here is either about the
persisted ToolRun's shape or about the never-fabricate constraint: no
company name should appear in a tool's output beyond the ones actually
present in the test's ProfileSnapshot fixture.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_run import ToolRun
from app.models.user import User
from app.tools import service
from app.tools.context import ContextUnavailable


def output_of(run: ToolRun) -> dict[str, Any]:
    assert run.output is not None
    return run.output


REAL_COMPANIES = {"Acme Corp"}
# Company-shaped names that must never appear -- if a fixture (or, in
# production, a real model) invents an employer, one of these classic
# placeholders is a likely shape for it to take.
FABRICATED_COMPANIES = [
    "Globex",
    "Initech",
    "Umbrella Corp",
    "TechCorp",
    "Wayne Enterprises",
    "Stark Industries",
    "Hooli",
]

_CORP_NAME = re.compile(r"\b[A-Z][\w&.]*(?:\s[A-Z][\w&.]*)*\s(?:Corp|Inc|LLC|Ltd)\b")


def assert_never_fabricates(output: dict[str, object]) -> None:
    text = json.dumps(output)
    for fake in FABRICATED_COMPANIES:
        assert fake not in text, f"output invented a company name: {fake!r}"
    for company_like in _CORP_NAME.findall(text):
        assert any(
            real in company_like for real in REAL_COMPANIES
        ), f"output mentions {company_like!r}, which isn't in the test profile"


async def test_profile_analysis_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, quota, _ = await service.run_tool(
        db_session, user=rich_profile_user, tool_id="profile.analysis", raw_input={}
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert isinstance(output["summary"], str) and output["summary"]
    assert 3 <= len(output["findings"]) <= 6
    for finding in output["findings"]:
        assert finding["severity"] in ("info", "warning", "critical")
    assert_never_fabricates(output)
    assert quota.metric == "tool_runs"


async def test_profile_analysis_requires_a_snapshot(
    db_session: AsyncSession, profile_user: User
) -> None:
    with pytest.raises(ContextUnavailable):
        await service.run_tool(
            db_session, user=profile_user, tool_id="profile.analysis", raw_input={}
        )


async def test_headline_optimizer_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="profile.headline_optimizer",
        raw_input={"target_role": "Staff Backend Engineer"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 5
    for variant in variants:
        assert len(variant["text"]) <= 220
        assert variant["rationale"]
        assert isinstance(variant["keywords"], list)
        assert variant["audience"]
    assert_never_fabricates(output)


async def test_headline_optimizer_works_without_a_target_role(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="profile.headline_optimizer",
        raw_input={},
    )
    assert run.status == "succeeded"
    assert len(output_of(run)["variants"]) == 5


async def test_about_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="profile.about_generator",
        raw_input={"target_role": "Staff Backend Engineer", "user_supplied_text": ""},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 3
    for variant in variants:
        assert len(variant["hook"]) + len(variant["body"]) + len(variant["cta"]) <= 2600
    assert_never_fabricates(output)


async def test_experience_optimizer_golden(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="profile.experience_optimizer",
        raw_input={},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    sections = output["sections"]
    assert len(sections) == 1
    bullets = sections[0]["bullets"]
    assert 3 <= len(bullets) <= 6
    for bullet in bullets:
        if bullet["flagged"]:
            assert bullet["flag_reason"]
    assert_never_fabricates(output)


async def test_skills_analyzer_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session, user=rich_profile_user, tool_id="profile.skills_analyzer", raw_input={}
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert output["columns"] == ["skill", "status", "relevance", "note"]
    for row in output["rows"]:
        assert row["status"] in ("have", "low-value", "missing")
        assert row["relevance"] in ("high", "medium", "low")
    assert_never_fabricates(output)


async def test_keyword_optimizer_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session, user=rich_profile_user, tool_id="profile.keyword_optimizer", raw_input={}
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert output["columns"] == ["keyword", "priority", "coverage", "placement"]
    for row in output["rows"]:
        assert row["priority"] in ("high", "medium", "low")
        assert row["coverage"] in ("present", "missing")
    assert_never_fabricates(output)


async def test_completeness_checker_golden(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="profile.completeness_checker",
        raw_input={},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert output["summary"]
    assert len(output["findings"]) >= 1
    assert_never_fabricates(output)
    # The score is Phase 2's deterministic engine, not the AI's -- the
    # tool never asks the model for a number, so nothing here should
    # look like the AI inventing its own score field.
    assert "score" not in output


async def test_completeness_checker_requires_a_snapshot(
    db_session: AsyncSession, profile_user: User
) -> None:
    with pytest.raises(ContextUnavailable):
        await service.run_tool(
            db_session,
            user=profile_user,
            tool_id="profile.completeness_checker",
            raw_input={},
        )
