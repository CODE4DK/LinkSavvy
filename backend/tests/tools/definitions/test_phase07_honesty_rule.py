"""Cross-cutting verification of Phase 7's honesty rule: every prompt
introduced in this phase (all seven engagement.* tools, all seven
career.* tools, and the resume segment resolver that isn't a
user-facing tool but still touches the gateway) must instruct the
model never to invent, fabricate, or falsely claim something -- an
employer, education, a credential, a tool, a metric, a date, or a
relationship/interaction that didn't happen.

This complements the per-tool honesty assertions already in
test_engagement_tools.py and test_career_tools.py (which check each
prompt's own specific wording); this file exists so a future prompt
added to either hub without any honesty language at all fails a single,
obvious test rather than slipping through unnoticed.
"""

from __future__ import annotations

from app.ai.prompts.loader import get_prompt

_PHASE_07_PROMPT_IDS = [
    "engagement.comment_generator.v1",
    "engagement.reply_generator.v1",
    "engagement.thought_leadership_comment.v1",
    "engagement.connection_request.v1",
    "engagement.follow_up.v1",
    "engagement.direct_message.v1",
    "engagement.recommendations.v1",
    "career.resume_analyzer.v1",
    "career.resume_builder.v1",
    "career.resume_jd_match.v1",
    "career.ats_optimizer.v1",
    "career.cover_letter.v1",
    "career.interview_prep.v1",
    "career.roadmap.v1",
    "career.resume_segment_resolver.v1",
]

_HONESTY_MARKERS = ("invent", "fabricat", "claim")


def test_every_phase_07_prompt_carries_an_honesty_rule() -> None:
    for prompt_id in _PHASE_07_PROMPT_IDS:
        body = get_prompt(prompt_id).body.lower()
        assert any(marker in body for marker in _HONESTY_MARKERS), (
            f"{prompt_id}'s prompt has no never-invent/fabricate/claim language -- "
            "every Phase 7 prompt must refuse to invent employment, education, "
            "credentials, tools, metrics, dates, or relationships that didn't happen"
        )


def test_every_engagement_and_career_prompt_is_covered_by_this_list() -> None:
    """Guards against a future tool being added to either hub without
    also being added to `_PHASE_07_PROMPT_IDS` above -- if this fails,
    add the new prompt id to the list (and confirm it carries the rule)
    rather than skipping it silently."""
    from app.ai.prompts.loader import get_registry

    all_ids = {template.id for template in get_registry().all()}
    phase_07_ids = {
        prompt_id
        for prompt_id in all_ids
        if prompt_id.startswith("engagement.") or prompt_id.startswith("career.")
    }
    assert phase_07_ids == set(_PHASE_07_PROMPT_IDS)
