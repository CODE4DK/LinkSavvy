"""Golden tests for the eight Content Hub tools: each runs for real
through `app/tools/service.py` against the real tool/prompt registries,
with only the AI provider faked. Mirrors
`tests/tools/definitions/test_profile_tools.py`'s pattern, including
the never-fabricate check against `rich_profile_user`'s real data.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.tools import service

from .test_profile_tools import assert_never_fabricates, output_of


async def test_post_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, quota = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.post_generator",
        raw_input={"topic": "code review culture", "post_type": "insight"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 3
    for variant in variants:
        assert variant["hook"]
        assert variant["body"]
        assert isinstance(variant["hashtags"], list)
        assert variant["estimated_read_time_seconds"] >= 1
    assert_never_fabricates(output)
    assert quota.metric == "tool_runs"


async def test_hook_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.hook_generator",
        raw_input={"topic": "code review culture", "post_type": "insight"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 10
    patterns = {v["pattern"] for v in variants}
    assert len(patterns) > 1, "hooks should span more than one pattern"
    for variant in variants:
        assert variant["hook"]
        assert variant["fold_preview"]
    assert_never_fabricates(output)


async def test_cta_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.cta_generator",
        raw_input={"post_body": "Code review isn't about catching bugs.", "goal": "comments"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 6
    levels = {v["demand_level"] for v in variants}
    assert levels <= {"low", "medium", "high"}
    assert_never_fabricates(output)


async def test_cta_generator_works_without_a_profile(
    db_session: AsyncSession, profile_user: User
) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=profile_user,
        tool_id="content.cta_generator",
        raw_input={"post_body": "A post with no profile grounding.", "goal": "dms"},
    )
    assert run.status == "succeeded"
    assert len(output_of(run)["variants"]) == 6


async def test_hashtag_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.hashtag_generator",
        raw_input={"post_body": "A post about code review.", "industry": "software"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert output["columns"] == ["tier", "hashtag", "note"]
    assert 3 <= len(output["rows"]) <= 8
    for row in output["rows"]:
        assert row["tier"] in ("broad", "niche", "community")
        assert row["hashtag"].startswith("#")
    assert output["stuffing_warning"]
    assert_never_fabricates(output)


async def test_post_rewriter_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.post_rewriter",
        raw_input={"post_body": "A post that needs tightening.", "goal": "tighter"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    sections = output["sections"]
    assert len(sections) == 2
    assert sections[0]["heading"] == "Rewritten post"
    assert sections[0]["body"]
    assert sections[1]["heading"] == "What changed"
    assert len(sections[1]["bullets"]) >= 1
    for bullet in sections[1]["bullets"]:
        if bullet["flagged"]:
            assert bullet["flag_reason"]
    assert_never_fabricates(output)


async def test_ideas_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.ideas_generator",
        raw_input={"how_many": 10, "time_horizon": "the next month"},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert output["columns"] == ["title", "angle", "post_type", "why", "difficulty"]
    assert 10 <= len(output["rows"]) <= 20
    for row in output["rows"]:
        assert row["difficulty"] in ("easy", "medium", "hard")
        assert row["why"]
    assert_never_fabricates(output)


async def test_carousel_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.carousel_generator",
        raw_input={"topic": "lessons from leading backend teams", "slide_count": 5},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert output["cover"]["headline"]
    assert 5 <= len(output["slides"]) <= 12
    for i, slide in enumerate(output["slides"], start=1):
        assert slide["index"] == i
        assert slide["headline"]
        assert slide["body"]
    assert output["closing"]["cta"]
    assert output["caption"]
    assert_never_fabricates(output)


async def test_repurpose_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="content.repurpose",
        raw_input={
            "source_content": "Code review isn't about catching bugs.",
            "source_format": "post",
            "target_format": "post",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert len(output["sections"]) >= 1
    assert output["sections"][0]["heading"]
    assert_never_fabricates(output)


async def test_repurpose_works_without_a_profile(
    db_session: AsyncSession, profile_user: User
) -> None:
    run, _ = await service.run_tool(
        db_session,
        user=profile_user,
        tool_id="content.repurpose",
        raw_input={
            "source_content": "Some source content with no profile at all.",
            "source_format": "post",
            "target_format": "comment_starter",
        },
    )
    assert run.status == "succeeded"
    assert output_of(run)["sections"]
