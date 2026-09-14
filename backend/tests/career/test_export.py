from __future__ import annotations

from app.career.export import export_resume_docx, export_resume_pdf
from app.career.parsers.layout import extract_resume_pdf_text
from app.career.parsers.segment import segment_resume_text
from app.career.schema import (
    ResumeContact,
    ResumeDocument,
    ResumeEducation,
    ResumeExperience,
    ResumeSkills,
    ResumeSource,
)
from app.profiles.parsers.documents import extract_docx_text
from app.profiles.schema import DatePart

SAMPLE_DOCUMENT = ResumeDocument(
    version=1,
    source=ResumeSource.BUILT,
    contact=ResumeContact(full_name="Jamie Rivera", email="jamie@example.com", phone="555-0100"),
    summary="Senior backend engineer with eight years of experience.",
    experiences=[
        ResumeExperience(
            company="Acme Corp",
            title="Senior Backend Engineer",
            start=DatePart(year=2020, month=1),
            is_current=True,
            bullets=["Led a team of eight engineers", "Reduced incident response time by half"],
        )
    ],
    education=[ResumeEducation(school="State University", degree="BS Computer Science")],
    skills=ResumeSkills(technical=["Python", "Kubernetes"]),
)


def test_pdf_export_round_trips_through_the_parser() -> None:
    pdf_bytes = export_resume_pdf(SAMPLE_DOCUMENT)
    assert pdf_bytes.startswith(b"%PDF-")

    text = extract_resume_pdf_text(pdf_bytes)
    result = segment_resume_text(text, source=ResumeSource.UPLOAD)

    assert result.document.contact is not None
    assert result.document.contact.full_name == "Jamie Rivera"
    assert len(result.document.experiences) == 1
    assert result.document.experiences[0].company == "Acme Corp"
    assert result.document.experiences[0].title == "Senior Backend Engineer"
    assert "Led a team of eight engineers" in result.document.experiences[0].bullets
    assert result.document.skills is not None
    assert "Python" in result.document.skills.technical


def test_docx_export_round_trips_through_the_parser() -> None:
    docx_bytes = export_resume_docx(SAMPLE_DOCUMENT)
    text = extract_docx_text(docx_bytes)
    result = segment_resume_text(text, source=ResumeSource.UPLOAD)

    assert result.document.contact is not None
    assert result.document.contact.full_name == "Jamie Rivera"
    assert len(result.document.experiences) == 1
    assert result.document.experiences[0].company == "Acme Corp"
