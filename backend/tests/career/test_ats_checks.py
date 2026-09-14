from __future__ import annotations

from app.career.ats_checks import ats_optimizer_postprocess, run_ats_checks

GOOD_RESUME = """\
Experience
Senior Backend Engineer, Acme Corp
Jan 2020 - Present
- Built the payments platform using Python and Kubernetes
"""

JD_TEXT = """\
Requirements
- Strong experience with Python and Kubernetes
- Experience with Terraform
"""


def test_flags_missing_experience_heading() -> None:
    findings = run_ats_checks(
        resume_text="Just some text with no headings at all.",
        job_description_text="",
        file_name="",
        detected_two_column_layout=False,
    )
    titles = {f["title"] for f in findings}
    assert 'No standard "Experience" heading found' in titles


def test_does_not_flag_a_standard_resume() -> None:
    findings = run_ats_checks(
        resume_text=GOOD_RESUME,
        job_description_text="",
        file_name="jamie-rivera-resume.pdf",
        detected_two_column_layout=False,
    )
    titles = {f["title"] for f in findings}
    assert 'No standard "Experience" heading found' not in titles
    assert "File name may not survive an upload pipeline" not in titles


def test_flags_two_column_layout() -> None:
    findings = run_ats_checks(
        resume_text=GOOD_RESUME,
        job_description_text="",
        file_name="",
        detected_two_column_layout=True,
    )
    titles = {f["title"] for f in findings}
    assert "Multi-column layout detected" in titles


def test_flags_unsafe_file_name() -> None:
    findings = run_ats_checks(
        resume_text=GOOD_RESUME,
        job_description_text="",
        file_name="Jamie Rivera Resume (final v2).pdf",
        detected_two_column_layout=False,
    )
    titles = {f["title"] for f in findings}
    assert "File name may not survive an upload pipeline" in titles


def test_flags_missing_keywords_from_job_description() -> None:
    findings = run_ats_checks(
        resume_text=GOOD_RESUME,
        job_description_text=JD_TEXT,
        file_name="",
        detected_two_column_layout=False,
    )
    keyword_findings = [f for f in findings if "keyword" in f["title"].lower()]
    assert len(keyword_findings) == 1
    assert "terraform" in keyword_findings[0]["description"].lower()


def test_ats_optimizer_postprocess_adds_findings() -> None:
    output: dict[str, object] = {"keyword_suggestions": []}
    result = ats_optimizer_postprocess(
        output,
        {
            "resume_text": "no headings here",
            "job_description_text": "",
            "file_name": "",
            "detected_two_column_layout": False,
        },
    )
    assert result["keyword_suggestions"] == []
    assert len(result["findings"]) >= 1
