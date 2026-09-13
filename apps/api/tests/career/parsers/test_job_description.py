from __future__ import annotations

from app.career.parsers.job_description import parse_job_description

SAMPLE_JD = """\
Senior Backend Engineer -- Remote (US)

About the role
We're looking for a Senior Backend Engineer to join our platform team
in Austin, TX.

Responsibilities
- Design and build distributed backend services
- Mentor junior engineers on the team
- Own the on-call rotation for the payments service

Requirements
- 5+ years of backend engineering experience
- Strong experience with Python and PostgreSQL
- Experience leading incident response

Preferred Qualifications
- Experience with Kubernetes
- Experience with event-driven architectures
"""


def test_parses_responsibilities() -> None:
    parsed = parse_job_description(SAMPLE_JD)
    assert len(parsed.responsibilities) == 3
    assert "Mentor junior engineers on the team" in parsed.responsibilities


def test_parses_required_and_preferred_qualifications() -> None:
    parsed = parse_job_description(SAMPLE_JD)
    assert any("Python" in q for q in parsed.required_qualifications)
    assert any("Kubernetes" in q for q in parsed.preferred_qualifications)


def test_detects_seniority() -> None:
    assert parse_job_description(SAMPLE_JD).seniority == "senior"


def test_detects_work_mode() -> None:
    assert parse_job_description(SAMPLE_JD).work_mode == "remote"


def test_detects_location() -> None:
    assert parse_job_description(SAMPLE_JD).location == "Austin, TX"


def test_extracts_keywords() -> None:
    keywords = parse_job_description(SAMPLE_JD).keywords
    assert "python" in keywords
    assert "kubernetes" in keywords
