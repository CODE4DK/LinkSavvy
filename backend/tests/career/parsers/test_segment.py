from __future__ import annotations

from app.career.parsers.segment import segment_resume_text
from app.career.schema import ResumeSource

SAMPLE_RESUME = """\
Jamie Rivera
jamie.rivera@example.com
(415) 555-0182
linkedin.com/in/jamierivera

Summary
Senior backend engineer with eight years leading distributed systems teams.

Experience
Senior Backend Engineer, Acme Corp
Jan 2020 - Present
- Led a team of eight engineers across two time zones
- Reduced incident response time by half
- Redesigned the on-call rotation to enforce clear ownership

Backend Engineer, Acme Corp
Jun 2017 - Dec 2019
- Built the payments reconciliation pipeline

Education
State University
BS Computer Science, Computer Science
2013 - 2017

Skills
Python, Go, SQL, Kubernetes, Leadership, Communication

Certifications
AWS Solutions Architect
Amazon Web Services

VOLUNTEER WORK
Mentored junior engineers through a local coding bootcamp.
"""


def test_parses_contact_info() -> None:
    result = segment_resume_text(SAMPLE_RESUME, source=ResumeSource.UPLOAD)
    contact = result.document.contact
    assert contact is not None
    assert contact.full_name == "Jamie Rivera"
    assert contact.email == "jamie.rivera@example.com"
    assert contact.phone is not None
    assert contact.linkedin_url is not None
    assert "linkedin.com/in/jamierivera" in contact.linkedin_url


def test_parses_summary() -> None:
    result = segment_resume_text(SAMPLE_RESUME, source=ResumeSource.UPLOAD)
    assert result.document.summary is not None
    assert "distributed systems" in result.document.summary


def test_parses_two_experience_entries_with_dates_and_bullets() -> None:
    result = segment_resume_text(SAMPLE_RESUME, source=ResumeSource.UPLOAD)
    experiences = result.document.experiences
    assert len(experiences) == 2

    first = experiences[0]
    assert first.title == "Senior Backend Engineer"
    assert first.company == "Acme Corp"
    assert first.start is not None and first.start.year == 2020 and first.start.month == 1
    assert first.is_current is True
    assert first.end is None
    assert len(first.bullets) == 3
    assert "Led a team of eight engineers across two time zones" in first.bullets

    second = experiences[1]
    assert second.start is not None and second.start.year == 2017
    assert second.end is not None and second.end.year == 2019
    assert second.is_current is False


def test_parses_education() -> None:
    result = segment_resume_text(SAMPLE_RESUME, source=ResumeSource.UPLOAD)
    assert len(result.document.education) == 1
    education = result.document.education[0]
    assert education.school == "State University"
    assert education.start is not None and education.start.year == 2013
    assert education.end is not None and education.end.year == 2017


def test_parses_skills_splitting_soft_from_technical() -> None:
    result = segment_resume_text(SAMPLE_RESUME, source=ResumeSource.UPLOAD)
    skills = result.document.skills
    assert skills is not None
    assert "Python" in skills.technical
    assert "Leadership" in skills.soft
    assert "Communication" in skills.soft


def test_parses_certifications() -> None:
    result = segment_resume_text(SAMPLE_RESUME, source=ResumeSource.UPLOAD)
    assert len(result.document.certifications) == 1
    assert result.document.certifications[0].name == "AWS Solutions Architect"


def test_unknown_heading_becomes_an_ambiguous_segment() -> None:
    result = segment_resume_text(SAMPLE_RESUME, source=ResumeSource.UPLOAD)
    guesses = {segment.heading_guess for segment in result.ambiguous_segments}
    assert "VOLUNTEER WORK" in guesses
    volunteer_segment = next(
        s for s in result.ambiguous_segments if s.heading_guess == "VOLUNTEER WORK"
    )
    assert "coding bootcamp" in volunteer_segment.raw_text


def test_experience_entry_with_no_date_range_is_ambiguous_not_guessed() -> None:
    text = """\
Experience
Freelance Consultant
Helped several startups design their backend architecture.
"""
    result = segment_resume_text(text, source=ResumeSource.UPLOAD)
    assert result.document.experiences == []
    assert len(result.ambiguous_segments) == 1
    assert result.ambiguous_segments[0].heading_guess == "experience"
    assert result.warnings
