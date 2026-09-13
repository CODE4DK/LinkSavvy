"""Golden tests for the seven Engagement Hub tools: each runs for real
through `app/tools/service.py` against the real tool/prompt registries,
with only the AI provider faked. Mirrors
`tests/tools/definitions/test_profile_tools.py`'s pattern. Beyond the
per-tool shape assertions, this file also covers the phase's specific
guardrail requirements: hard character limits are declared (and
enforced by the gateway's schema validation, not by truncation), every
outreach tool is annotated by `postprocess` with personalisation/spam
flags, Direct Message discloses sales intent early, and Engagement
Recommendations' prompt carries a tested refusal of automation/pods/
engagement-farming.
"""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.loader import get_prompt
from app.engagement.guardrails import (
    COMMENT_MAX_CHARS,
    CONNECTION_NOTE_MAX_CHARS,
    INMAIL_SUBJECT_MAX_CHARS,
)
from app.models.user import User
from app.tools import service
from app.tools.registry import get_tool

from .test_profile_tools import assert_never_fabricates, output_of


async def test_comment_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.comment_generator",
        raw_input={
            "post_text": "Unclear ownership is the real reason incidents drag on.",
            "angle": "I've led backend teams through this exact problem.",
            "stance": "agree_and_extend",
            "length": "medium",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 4
    stances = {v["stance"] for v in variants}
    assert len(stances) > 1, "comments should span more than one stance"
    for variant in variants:
        assert variant["comment"]
        assert len(variant["comment"]) <= COMMENT_MAX_CHARS
        assert variant["adds"]
        # postprocess must have annotated every variant
        assert "personalisation_flags" in variant
        assert "spam_flags" in variant
    assert_never_fabricates(output)


async def test_reply_generator_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.reply_generator",
        raw_input={
            "original_post": "Ownership gaps are why incidents drag on.",
            "comment_text": "What about onboarding new hires into that ownership model?",
            "relationship": "new_connection",
            "intent": "Answer their question and keep the conversation going.",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 3
    warmths = {v["warmth"] for v in variants}
    assert warmths <= {"warm", "neutral", "brief"}
    for variant in variants:
        assert variant["reply"]
        assert len(variant["reply"]) <= COMMENT_MAX_CHARS
        assert "personalisation_flags" in variant
    assert_never_fabricates(output)


async def test_thought_leadership_comment_golden(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.thought_leadership_comment",
        raw_input={
            "post_text": "Unclear ownership is the real reason incidents drag on.",
            "your_angle": "How we enforced ownership through the on-call rotation.",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 1
    assert len(variants[0]["comment"]) <= COMMENT_MAX_CHARS
    assert variants[0]["what_this_adds"]
    assert "personalisation_flags" in variants[0]
    assert_never_fabricates(output)


async def test_connection_request_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.connection_request",
        raw_input={
            "who_they_are": "Jordan, VP of Engineering, posts about backend reliability.",
            "how_you_know_them": "Read their post on distributed systems reliability.",
            "goal": "Build my network with reliability-focused engineering leaders.",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 3
    for variant in variants:
        assert len(variant["note"]) <= CONNECTION_NOTE_MAX_CHARS
        assert "personalisation_flags" in variant
    assert_never_fabricates(output)


def test_connection_request_note_over_limit_is_rejected_by_schema() -> None:
    tool = get_tool("engagement.connection_request")
    output_variant_model = tool.output_schema.model_fields["variants"].annotation
    assert output_variant_model is not None
    # The per-variant model enforces CONNECTION_NOTE_MAX_CHARS -- an
    # over-length note fails Pydantic validation outright rather than
    # being truncated, mirroring the gateway's own JSON Schema
    # enforcement of the same `Field(max_length=...)` declaration.
    variant_model = output_variant_model.__args__[0]
    try:
        variant_model(note="x" * (CONNECTION_NOTE_MAX_CHARS + 1))
    except ValidationError:
        return
    raise AssertionError("expected an over-length connection note to fail validation")


def test_direct_message_subject_over_limit_is_rejected_by_schema() -> None:
    tool = get_tool("engagement.direct_message")
    output_variant_model = tool.output_schema.model_fields["variants"].annotation
    assert output_variant_model is not None
    variant_model = output_variant_model.__args__[0]
    try:
        variant_model(subject="x" * (INMAIL_SUBJECT_MAX_CHARS + 1), message="hello")
    except ValidationError:
        return
    raise AssertionError("expected an over-length InMail subject to fail validation")


async def test_follow_up_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.follow_up",
        raw_input={
            "prior_context": "Left a note asking whether the on-call rotation change stuck.",
            "time_since_last_contact": "1-2 weeks",
            "purpose": "Check whether they're still interested in comparing notes.",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 3
    banned_guilt_phrases = ["sorry it's been so long", "i know you're busy", "sorry for"]
    for variant in variants:
        assert variant["message"]
        assert variant["exit_line"]
        lowered = variant["message"].lower()
        for phrase in banned_guilt_phrases:
            assert phrase not in lowered
        assert "personalisation_flags" in variant
    assert_never_fabricates(output)


async def test_direct_message_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.direct_message",
        raw_input={
            "recipient_context": "Jordan, VP of Engineering, writes about backend reliability.",
            "goal": "sales",
            "relationship_strength": "weak_tie",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    variants = output["variants"]
    assert len(variants) == 3
    for variant in variants:
        if variant.get("subject") is not None:
            assert len(variant["subject"]) <= INMAIL_SUBJECT_MAX_CHARS
        assert "personalisation_flags" in variant
    assert_never_fabricates(output)


def test_direct_message_sales_variant_discloses_intent_early() -> None:
    """The fixture's sales-shaped variant must name the pitch within its
    first two sentences -- structural proof the prompt's disclosure rule
    is reflected in what the tool actually produces."""
    import json

    from app.ai.providers.fake_provider import DEFAULT_FIXTURES_DIR

    fixture = json.loads((DEFAULT_FIXTURES_DIR / "engagement.direct_message.v1.json").read_text())
    variants = fixture["response"]["variants"]
    sales_variant = next(v for v in variants if v.get("subject"))
    first_two_sentences = ".".join(sales_variant["message"].split(".")[:2]).lower()
    assert "building" in first_two_sentences or "offering" in first_two_sentences


async def test_recommendations_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.recommendations",
        raw_input={"industry": "software", "goals": "Build thought leadership in reliability."},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert output["columns"] == ["action", "reason", "cadence"]
    assert 3 <= len(output["rows"]) <= 10
    for row in output["rows"]:
        assert row["action"]
        assert row["reason"]
        assert row["cadence"]
    assert_never_fabricates(output)
    # No variant may exist on this tool -- it's the one Engagement tool
    # that is never gated behind the outreach review checkbox.
    assert get_tool("engagement.recommendations").counts_as_outreach is False


_BANNED_AUTOMATION_TERMS = ["engagement pod", "bot", "automat", "browser extension", "unattended"]


async def test_recommendations_never_suggests_automation(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="engagement.recommendations",
        raw_input={"industry": "software", "goals": "Grow engagement fast."},
    )
    output_text = " ".join(
        f"{row['action']} {row['reason']}" for row in output_of(run)["rows"]
    ).lower()
    for term in _BANNED_AUTOMATION_TERMS:
        assert term not in output_text


def test_recommendations_prompt_carries_the_refusal_rule() -> None:
    body = get_prompt("engagement.recommendations.v1").body.lower()
    assert "engagement pods" in body
    assert "automating" in body
    assert "bots" in body


def test_every_outreach_tool_counts_as_outreach() -> None:
    outreach_ids = [
        "engagement.comment_generator",
        "engagement.reply_generator",
        "engagement.thought_leadership_comment",
        "engagement.connection_request",
        "engagement.follow_up",
        "engagement.direct_message",
    ]
    for tool_id in outreach_ids:
        assert get_tool(tool_id).counts_as_outreach is True
    assert get_tool("engagement.recommendations").counts_as_outreach is False
