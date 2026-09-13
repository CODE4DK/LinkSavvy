"""Deterministic resume segmentation: heading detection, then per-
section parsing of contact info, dates, and bullets. Reads plain text
already produced by `app.career.parsers.layout` (PDF) or
`app.profiles.parsers.documents.extract_docx_text` (DOCX) or a direct
paste -- this module never touches file bytes itself.

Whatever this pass cannot confidently classify -- an unrecognised
section heading, or an experience entry with no parseable date range --
is collected as an `AmbiguousSegment` rather than guessed at. Those (and
only those) are what `app.career.parsers.resolve` sends to the AI
gateway, in one batched call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.career.schema import (
    ProvenanceSource,
    ResumeCertification,
    ResumeContact,
    ResumeDocument,
    ResumeEducation,
    ResumeExperience,
    ResumeFieldProvenance,
    ResumeProject,
    ResumeSkills,
    ResumeSource,
)
from app.profiles.schema import DatePart

_KNOWN_HEADINGS = {
    "summary": "summary",
    "professional summary": "summary",
    "objective": "summary",
    "profile": "summary",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "work history": "experience",
    "education": "education",
    "skills": "skills",
    "technical skills": "skills",
    "core competencies": "skills",
    "certifications": "certifications",
    "licenses & certifications": "certifications",
    "licenses and certifications": "certifications",
    "projects": "projects",
    "awards": "awards",
    "honors": "awards",
    "honors & awards": "awards",
    "publications": "publications",
}

_SOFT_SKILL_KEYWORDS = {
    "leadership",
    "communication",
    "teamwork",
    "collaboration",
    "mentoring",
    "mentorship",
    "problem solving",
    "problem-solving",
    "time management",
    "adaptability",
    "critical thinking",
    "public speaking",
    "negotiation",
    "conflict resolution",
    "stakeholder management",
}

_BULLET_PREFIXES = ("•", "‣", "●", "◦", "▪", "- ", "* ")

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_DATE_RANGE_RE = re.compile(
    r"(?P<start>[A-Za-z]{3,9}\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4})\s*[-–—to]+\s*"
    r"(?P<end>Present|present|Current|current|[A-Za-z]{3,9}\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4})"
)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(\+?\d[\d\-.\s()]{8,}\d)")
_LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/\S+", re.IGNORECASE)
_WEBSITE_RE = re.compile(r"(?:https?://)?(?:www\.)?[\w-]+\.[a-z]{2,}(?:/\S*)?", re.IGNORECASE)


def _parse_month_year(token: str) -> DatePart | None:
    token = token.strip().rstrip(".")
    match = re.match(r"^([A-Za-z]{3,9})\.?\s+(\d{4})$", token)
    if match:
        month = _MONTHS.get(match.group(1)[:3].lower())
        return DatePart(year=int(match.group(2)), month=month)
    match = re.match(r"^(\d{1,2})/(\d{4})$", token)
    if match:
        return DatePart(year=int(match.group(2)), month=int(match.group(1)))
    match = re.match(r"^(\d{4})$", token)
    if match:
        return DatePart(year=int(match.group(1)))
    return None


def _find_date_range(line: str) -> tuple[DatePart | None, DatePart | None, bool] | None:
    match = _DATE_RANGE_RE.search(line)
    if not match:
        return None
    start = _parse_month_year(match.group("start"))
    end_token = match.group("end")
    is_current = end_token.lower() in ("present", "current")
    end = None if is_current else _parse_month_year(end_token)
    return start, end, is_current


def _strip_bullet(line: str) -> str | None:
    stripped = line.lstrip()
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return None


def _split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def _looks_like_heading(line: str) -> str | None:
    key = line.strip().lower().strip(":")
    return _KNOWN_HEADINGS.get(key)


def _split_sections(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Returns (header_lines, {canonical_section_name: lines}). An
    unrecognised heading-shaped line (short, title-case or all-caps, no
    trailing punctuation) still opens a new block, kept under its own
    literal heading text -- that block becomes an ambiguous segment
    rather than being silently dropped or mis-filed."""
    heading_positions: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not line:
            continue
        canonical = _looks_like_heading(line)
        if canonical is not None:
            heading_positions.append((i, canonical))
        elif _looks_like_unknown_heading(line):
            heading_positions.append((i, f"custom:{line.strip()}"))

    header_lines = lines[: heading_positions[0][0]] if heading_positions else lines
    sections: dict[str, list[str]] = {}
    for idx, (start_i, name) in enumerate(heading_positions):
        end_i = heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        sections.setdefault(name, []).extend(lines[start_i + 1 : end_i])
    return header_lines, sections


def _looks_like_unknown_heading(line: str) -> bool:
    """Deliberately conservative: only an ALL-CAPS short line counts.
    Title-case is too common in ordinary resume content (a school name,
    a job title) to use as a heading signal without a false-positive
    rate that would misfile real content as a section boundary."""
    words = line.split()
    if not (1 <= len(words) <= 5):
        return False
    if any(char.isdigit() for char in line):
        return False
    if _strip_bullet(line) is not None:
        return False
    if _find_date_range(line) is not None:
        return False
    if _EMAIL_RE.search(line) or _PHONE_RE.search(line) or _LINKEDIN_RE.search(line):
        return False
    return line.isupper() and any(char.isalpha() for char in line)


def _split_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _parse_contact(header_lines: list[str]) -> ResumeContact:
    contact = ResumeContact()
    non_empty = [line for line in header_lines if line]
    for line in non_empty:
        if contact.email is None:
            email_match = _EMAIL_RE.search(line)
            if email_match:
                contact.email = email_match.group(0)
        if contact.phone is None:
            phone_match = _PHONE_RE.search(line)
            if phone_match and len(re.sub(r"\D", "", phone_match.group(0))) >= 7:
                contact.phone = phone_match.group(0).strip()
        if contact.linkedin_url is None:
            linkedin_match = _LINKEDIN_RE.search(line)
            if linkedin_match:
                contact.linkedin_url = linkedin_match.group(0)
        if (
            contact.website_url is None
            and not _EMAIL_RE.search(line)
            and not _LINKEDIN_RE.search(line)
        ):
            website_match = _WEBSITE_RE.search(line)
            if website_match:
                contact.website_url = website_match.group(0)
    if non_empty and contact.full_name is None:
        first = non_empty[0]
        if not _EMAIL_RE.search(first) and not _PHONE_RE.search(first):
            contact.full_name = first
    return contact


@dataclass
class AmbiguousSegment:
    """A block of resume text this pass could not confidently turn into
    structured fields -- handed, batched, to the one-shot AI resolver."""

    segment_id: str
    heading_guess: str
    raw_text: str


@dataclass
class SegmentResult:
    document: ResumeDocument
    ambiguous_segments: list[AmbiguousSegment] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _parse_experience_block(
    block: list[str], *, segment_id: str
) -> tuple[ResumeExperience | None, AmbiguousSegment | None]:
    date_idx = next((i for i, line in enumerate(block) if _find_date_range(line)), None)
    if date_idx is None:
        return None, AmbiguousSegment(
            segment_id=segment_id, heading_guess="experience", raw_text="\n".join(block)
        )

    header_line = block[date_idx]
    dates = _find_date_range(header_line)
    assert dates is not None
    start, end, is_current = dates
    header_text = _DATE_RANGE_RE.sub("", header_line).strip(" -–—|,")

    title: str | None = None
    company: str | None = None
    if date_idx > 0:
        # The date range shares its line with company/title, or sits on
        # the line right after a "Title, Company" / "Title | Company"
        # header -- either shape is common in real resumes.
        prior = block[date_idx - 1]
        title, _, company = _split_title_company(prior)
    if header_text:
        parsed_title, _, parsed_company = _split_title_company(header_text)
        title = title or parsed_title
        company = company or parsed_company

    bullets: list[str] = []
    for line in block[date_idx + 1 :]:
        bullet_text = _strip_bullet(line)
        bullets.append(bullet_text if bullet_text is not None else line)

    return (
        ResumeExperience(
            company=company,
            title=title,
            start=start,
            end=end,
            is_current=is_current,
            bullets=bullets,
        ),
        None,
    )


def _split_title_company(line: str) -> tuple[str | None, str | None, str | None]:
    for sep in (" | ", " — ", " – ", ", ", " at "):
        if sep in line:
            left, _, right = line.partition(sep)
            return left.strip() or None, sep, right.strip() or None
    return line.strip() or None, None, None


def _parse_education_block(block: list[str]) -> ResumeEducation:
    date_idx = next((i for i, line in enumerate(block) if _find_date_range(line)), None)
    start = end = None
    if date_idx is not None:
        dates = _find_date_range(block[date_idx])
        if dates:
            start, end, _ = dates

    header_lines = [line for i, line in enumerate(block) if i != date_idx]
    school = header_lines[0] if header_lines else None
    degree = None
    field_of_study = None
    if len(header_lines) > 1:
        degree_line = header_lines[1]
        if "," in degree_line:
            degree, _, field_of_study = (part.strip() for part in degree_line.partition(","))
        else:
            degree = degree_line

    return ResumeEducation(school=school, degree=degree, field=field_of_study, start=start, end=end)


def _parse_skills(lines: list[str]) -> ResumeSkills:
    raw = re.split(r"[,;\n•]", " ".join(lines))
    skills = ResumeSkills()
    for item in raw:
        item = item.strip(" .")
        if not item:
            continue
        if item.lower() in _SOFT_SKILL_KEYWORDS:
            skills.soft.append(item)
        else:
            skills.technical.append(item)
    return skills


def _parse_certification_block(block: list[str]) -> ResumeCertification:
    name = block[0] if block else None
    issuer = block[1] if len(block) > 1 else None
    return ResumeCertification(name=name, issuer=issuer)


def _parse_project_block(block: list[str]) -> ResumeProject:
    name = block[0] if block else None
    description_lines = []
    for line in block[1:]:
        bullet_text = _strip_bullet(line)
        description_lines.append(bullet_text if bullet_text is not None else line)
    return ResumeProject(name=name, description="\n".join(description_lines) or None)


def segment_resume_text(text: str, *, source: ResumeSource) -> SegmentResult:
    lines = _split_lines(text)
    header_lines, sections = _split_sections(lines)

    document = ResumeDocument(version=1, source=source)
    document.contact = _parse_contact(header_lines)
    warnings: list[str] = []
    ambiguous: list[AmbiguousSegment] = []
    provenance: dict[str, ResumeFieldProvenance] = {}
    confident = ResumeFieldProvenance(source=ProvenanceSource.DETERMINISTIC_PARSE, confidence=0.9)

    if document.contact.full_name:
        provenance["/contact/full_name"] = confident

    for name, section_lines in sections.items():
        if name == "summary":
            document.summary = "\n".join(line for line in section_lines if line).strip() or None
            if document.summary:
                provenance["/summary"] = confident
        elif name == "experience":
            for i, block in enumerate(_split_blocks(section_lines)):
                segment_id = f"experience-{i}"
                experience, ambiguous_segment = _parse_experience_block(
                    block, segment_id=segment_id
                )
                if experience is not None:
                    document.experiences.append(experience)
                    provenance[f"/experiences/{len(document.experiences) - 1}"] = confident
                else:
                    assert ambiguous_segment is not None
                    ambiguous.append(ambiguous_segment)
                    warnings.append(
                        f"Could not find a date range in an experience entry: "
                        f"{' | '.join(block)[:120]}"
                    )
        elif name == "education":
            for block in _split_blocks(section_lines):
                document.education.append(_parse_education_block(block))
        elif name == "skills":
            document.skills = _parse_skills(section_lines)
        elif name == "certifications":
            for block in _split_blocks(section_lines):
                document.certifications.append(_parse_certification_block(block))
        elif name == "projects":
            for block in _split_blocks(section_lines):
                document.projects.append(_parse_project_block(block))
        elif name in ("awards", "publications"):
            # Deterministic parsing of awards/publications is low-value
            # (they're short, free-form, and rarely need structured
            # fields the way experience/education do) -- treat the whole
            # section as one ambiguous segment for the AI pass, which can
            # place each entry correctly.
            raw_text = "\n".join(line for line in section_lines if line)
            if raw_text:
                ambiguous.append(
                    AmbiguousSegment(segment_id=f"{name}-0", heading_guess=name, raw_text=raw_text)
                )
        elif name.startswith("custom:"):
            heading = name.removeprefix("custom:")
            raw_text = "\n".join(line for line in section_lines if line)
            if raw_text:
                ambiguous.append(
                    AmbiguousSegment(
                        segment_id=f"custom-{len(ambiguous)}",
                        heading_guess=heading,
                        raw_text=raw_text,
                    )
                )

    document.field_provenance = provenance
    return SegmentResult(document=document, ambiguous_segments=ambiguous, warnings=warnings)
