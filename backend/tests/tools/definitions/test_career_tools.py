"""Golden tests for the seven Career Hub tools: each runs for real
through `app/tools/service.py` against the real tool/prompt registries,
with only the AI provider faked. Mirrors
`tests/tools/definitions/test_engagement_tools.py`'s pattern. Also
covers this phase's specific requirements: resume_analyzer's
deterministic findings are labelled `rule_based`, resume_jd_match's
percentage is reconstructible from its own components, ats_optimizer
never lets the AI add an unsupported skill, and every prompt carries
the honesty rule (tested textually against the prompt body).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.loader import get_prompt
from app.models.user import User
from app.tools import service
from app.tools.registry import get_tool

from .test_profile_tools import assert_never_fabricates, output_of

SAMPLE_RESUME = """\
Jamie Rivera
jamie.rivera@example.com

Experience
Senior Backend Engineer, Acme Corp
Jan 2020 - Present
- Led a team of eight engineers
- Reduced incident response time by half

Skills
Python, SQL
"""

SAMPLE_JD = """\
Senior Backend Engineer

Requirements
- 5+ years of backend engineering experience
- Experience leading incident response

Preferred Qualifications
- Experience with Terraform
"""


async def test_resume_analyzer_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="career.resume_analyzer",
        raw_input={"resume_text": SAMPLE_RESUME},
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert 0 <= output["score"] <= 100
    assert len(output["dimension_scores"]) == 6
    # The deterministic pass runs on SAMPLE_RESUME (short, no metrics on
    # most lines) and must be clearly labelled apart from the AI's own
    # finding.
    assert any(f.get("rule_based") is True for f in output["findings"])
    assert any("rule_based" not in f for f in output["findings"])
    assert_never_fabricates(output)


async def test_resume_builder_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="career.resume_builder",
        raw_input={
            "section": "summary",
            "context_text": "Senior backend engineer, led team of eight at Acme Corp.",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert len(output["variants"]) == 3
    for variant in output["variants"]:
        assert variant["text"]
    assert_never_fabricates(output)


async def test_resume_jd_match_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="career.resume_jd_match",
        raw_input={"resume_text": SAMPLE_RESUME, "job_description_text": SAMPLE_JD},
    )
    assert run.status == "succeeded"
    output = output_of(run)

    components = output["component_scores"]
    assert len(components) == 5
    assert abs(sum(c["weight"] for c in components) - 1.0) < 1e-6
    for component in components:
        assert abs(component["contribution"] - component["weight"] * component["score"]) < 1e-6
    reconstructed = round(sum(c["contribution"] for c in components))
    assert output["overall_match"] == reconstructed

    # postprocess must have derived the generic table shape.
    assert output["columns"] == ["requirement", "status", "detail"]
    statuses = {row["status"] for row in output["rows"]}
    assert statuses <= {"matched", "missing", "transferable"}
    assert_never_fabricates(output)


async def test_ats_optimizer_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="career.ats_optimizer",
        raw_input={
            "resume_text": SAMPLE_RESUME,
            "job_description_text": SAMPLE_JD,
            "file_name": "Jamie Rivera Resume.pdf",
            "detected_two_column_layout": True,
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    # findings are 100% deterministic (postprocess), never from the AI's
    # own strict schema (which only ever returns keyword_suggestions).
    finding_titles = {f["title"] for f in output["findings"]}
    assert "Multi-column layout detected" in finding_titles
    assert "File name may not survive an upload pipeline" in finding_titles
    assert isinstance(output["keyword_suggestions"], list)
    assert_never_fabricates(output)


async def test_ats_optimizer_prompt_refuses_to_invent_skills() -> None:
    body = get_prompt("career.ats_optimizer.v1").body.lower()
    assert "never suggest adding a skill" in body


async def test_cover_letter_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="career.cover_letter",
        raw_input={
            "resume_text": SAMPLE_RESUME,
            "job_description_text": SAMPLE_JD,
            "tone": "confident",
            "length": "medium",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert len(output["sections"]) == 2
    assert output["sections"][0]["heading"] == "Cover Letter"
    assert output["sections"][1]["heading"] == "Email version"
    assert len(output["sections"][1]["body"]) < len(output["sections"][0]["body"])
    assert_never_fabricates(output)


async def test_interview_prep_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="career.interview_prep",
        raw_input={
            "job_description_text": SAMPLE_JD,
            "interview_type": "behavioural",
            "seniority": "senior",
            "resume_text": SAMPLE_RESUME,
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    messages = output["messages"]
    assert messages[-1]["role"] == "candidate"
    assert sum(1 for m in messages if m["role"] == "interviewer") >= 3
    assert_never_fabricates(output)


async def test_roadmap_golden(db_session: AsyncSession, rich_profile_user: User) -> None:
    run, _, _ = await service.run_tool(
        db_session,
        user=rich_profile_user,
        tool_id="career.roadmap",
        raw_input={
            "current_role": "Senior Backend Engineer",
            "target_role": "Engineering Manager",
            "time_horizon": "8 months",
        },
    )
    assert run.status == "succeeded"
    output = output_of(run)
    assert 2 <= len(output["sections"]) <= 5
    for phase in output["sections"]:
        assert len(phase["bullets"]) >= 4
    flagged = [
        bullet for phase in output["sections"] for bullet in phase["bullets"] if bullet["flagged"]
    ]
    assert all(bullet["flag_reason"] for bullet in flagged)
    assert_never_fabricates(output)


def test_every_career_tool_never_invents_rule_is_in_its_prompt() -> None:
    tool_ids_and_phrases = [
        ("career.resume_analyzer", "never invent a job"),
        ("career.resume_builder", "never invent an employer"),
        ("career.resume_jd_match", "never claim the resume shows"),
        ("career.cover_letter", "never invent an employer"),
        ("career.interview_prep", "never an invented example"),
        ("career.roadmap", "never invent a credential"),
    ]
    for tool_id, phrase in tool_ids_and_phrases:
        prompt_id = get_tool(tool_id).prompt_id
        body = get_prompt(prompt_id).body.lower()
        assert phrase in body, f"{tool_id}'s prompt is missing its honesty rule"
