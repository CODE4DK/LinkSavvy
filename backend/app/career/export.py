"""ATS-safe resume export: single column, no tables, no text boxes, no
images, standard section headings, an embedded standard font. Both
formats render the exact same structure so either one, fed back
through this phase's own parser, recovers it -- see the round-trip
test in tests/career/test_export.py, which is what actually enforces
"ATS-safe" here rather than just asserting it in a docstring.
"""

from __future__ import annotations

import io

from docx import Document as DocxDocument
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.career.schema import ResumeDocument

_PAGE_WIDTH, _PAGE_HEIGHT = LETTER
_MARGIN = 60
_BODY_SIZE = 11
_HEADING_SIZE = 13
_NAME_SIZE = 18
_LINE_HEIGHT = 15
_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"


def _date_label(date: object) -> str:
    if date is None:
        return ""
    year = getattr(date, "year", None)
    month = getattr(date, "month", None)
    if year is None:
        return ""
    return f"{month:02d}/{year}" if month else str(year)


def _experience_lines(document: ResumeDocument) -> list[tuple[str, bool]]:
    """Returns (line, is_heading) pairs for the EXPERIENCE section."""
    lines: list[tuple[str, bool]] = []
    for exp in document.experiences:
        header = " | ".join(part for part in (exp.title, exp.company) if part)
        start = _date_label(exp.start)
        end = "Present" if exp.is_current else _date_label(exp.end)
        date_range = f"{start} - {end}" if start or end else ""
        if header:
            lines.append((header, False))
        if date_range:
            lines.append((date_range, False))
        for bullet in exp.bullets:
            lines.append((f"- {bullet}", False))
    return lines


def _build_plain_sections(document: ResumeDocument) -> list[tuple[str, list[str]]]:
    """Standard-headed, single-column sections -- the same shape whether
    this ends up as a PDF or a DOCX."""
    sections: list[tuple[str, list[str]]] = []

    if document.summary:
        sections.append(("SUMMARY", [document.summary]))

    if document.experiences:
        exp_lines = [line for line, _ in _experience_lines(document)]
        sections.append(("EXPERIENCE", exp_lines))

    if document.education:
        edu_lines = []
        for edu in document.education:
            header = " | ".join(part for part in (edu.degree, edu.school) if part)
            if header:
                edu_lines.append(header)
        sections.append(("EDUCATION", edu_lines))

    if document.skills:
        all_skills = document.skills.technical + document.skills.tools + document.skills.soft
        if all_skills:
            sections.append(("SKILLS", [", ".join(all_skills)]))

    if document.certifications:
        cert_lines = [c.name for c in document.certifications if c.name]
        sections.append(("CERTIFICATIONS", cert_lines))

    return sections


def export_resume_pdf(document: ResumeDocument) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    y = _PAGE_HEIGHT - _MARGIN

    def _new_page_if_needed() -> None:
        nonlocal y
        if y < _MARGIN:
            pdf.showPage()
            pdf.setFont(_FONT, _BODY_SIZE)
            y = _PAGE_HEIGHT - _MARGIN

    contact = document.contact
    if contact and contact.full_name:
        pdf.setFont(_FONT_BOLD, _NAME_SIZE)
        pdf.drawString(_MARGIN, y, contact.full_name)
        y -= _LINE_HEIGHT * 1.5
        pdf.setFont(_FONT, _BODY_SIZE)
        contact_line = " | ".join(
            part for part in (contact.email, contact.phone, contact.location) if part
        )
        if contact_line:
            pdf.drawString(_MARGIN, y, contact_line)
            y -= _LINE_HEIGHT * 1.5

    for heading, lines in _build_plain_sections(document):
        _new_page_if_needed()
        pdf.setFont(_FONT_BOLD, _HEADING_SIZE)
        pdf.drawString(_MARGIN, y, heading)
        y -= _LINE_HEIGHT
        pdf.setFont(_FONT, _BODY_SIZE)
        for line in lines:
            _new_page_if_needed()
            pdf.drawString(_MARGIN, y, line[:110])
            y -= _LINE_HEIGHT
        y -= _LINE_HEIGHT * 0.5

    pdf.save()
    return buffer.getvalue()


def export_resume_docx(document: ResumeDocument) -> bytes:
    docx = DocxDocument()

    contact = document.contact
    if contact and contact.full_name:
        docx.add_paragraph(contact.full_name)
        contact_line = " | ".join(
            part for part in (contact.email, contact.phone, contact.location) if part
        )
        if contact_line:
            docx.add_paragraph(contact_line)

    for heading, lines in _build_plain_sections(document):
        docx.add_paragraph(heading)
        for line in lines:
            docx.add_paragraph(line)

    buffer = io.BytesIO()
    docx.save(buffer)
    return buffer.getvalue()
