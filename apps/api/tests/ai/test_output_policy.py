from __future__ import annotations

import pytest

from app.ai.safety.output_policy import OutputPolicyViolation, check_output_policy


def test_benign_text_passes() -> None:
    check_output_policy(
        "Consider highlighting your leadership experience and quantifying impact with metrics."
    )  # no exception


@pytest.mark.parametrize(
    "text",
    [
        "Set up a bot to auto-connect with recruiters every day.",
        "You could automatically comment on posts to boost visibility.",
        "Use a headless browser to interact with LinkedIn on your behalf.",
    ],
)
def test_automation_instructions_are_blocked(text: str) -> None:
    with pytest.raises(OutputPolicyViolation) as excinfo:
        check_output_policy(text)
    assert excinfo.value.category == "automation"
    assert excinfo.value.code.value == "AI_POLICY_BLOCKED"
    assert excinfo.value.status_code == 422


@pytest.mark.parametrize(
    "text",
    [
        "You could pretend to be a hiring manager to get more responses.",
        "Pose as a recruiter when reaching out to candidates.",
    ],
)
def test_impersonation_instructions_are_blocked(text: str) -> None:
    with pytest.raises(OutputPolicyViolation) as excinfo:
        check_output_policy(text)
    assert excinfo.value.category == "impersonation"


@pytest.mark.parametrize(
    "text",
    [
        "You could fake a certification to look more qualified.",
        "Make up a metric like '300% growth' to sound impressive.",
        "Invent a job title that sounds more senior than your actual role.",
    ],
)
def test_fabrication_instructions_are_blocked(text: str) -> None:
    with pytest.raises(OutputPolicyViolation) as excinfo:
        check_output_policy(text)
    assert excinfo.value.category == "fabrication"


def test_violation_details_never_include_raw_text() -> None:
    with pytest.raises(OutputPolicyViolation) as excinfo:
        check_output_policy("fabricate an award you never won")
    assert "fabricate an award" not in str(excinfo.value.details)
