"""Deterministic parser for a pasted LinkedIn-profile-shaped text block.

No network calls, no browser, no LinkedIn HTML — this only ever sees text
the user pasted into a textbox themselves. Section boundaries are found
by known headings; everything inside a section is split by blank lines
into entries, then picked apart with a handful of regexes tuned to the
shape LinkedIn's own "copy profile text" output takes (title, then
"Company · Employment type", then a date range, then an optional
location, then a description with bullet lines).

The parser is deliberately conservative: when it cannot confidently
segment something, it emits a warning and keeps the raw text in the
nearest sensible field rather than dropping it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.profiles.schema import (
    Certification,
    DatePart,
    Education,
    Experience,
    FieldProvenance,
    Identity,
    Language,
    ProfileSnapshot,
    ProfileSource,
    Skill,
)

KNOWN_HEADINGS = {
    "about": "about",
    "experience": "experience",
    "education": "education",
    "licenses & certifications": "certifications",
    "licenses and certifications": "certifications",
    "certifications": "certifications",
    "licenses": "certifications",
    "skills": "skills",
    "languages": "languages",
    "projects": "projects",
}

EMPLOYMENT_TYPES = [
    "Full-time",
    "Part-time",
    "Self-employed",
    "Freelance",
    "Contract",
    "Internship",
    "Apprenticeship",
    "Seasonal",
]

_BULLET_PREFIXES = ("•", "‣", "●", "◦", "- ", "* ")

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
    r"^(?P<start>[A-Za-z]{3,9}\s+\d{4}|\d{4})\s*[-–—]\s*"
    r"(?P<end>Present|present|[A-Za-z]{3,9}\s+\d{4}|\d{4})"
    r"(?:\s*·\s*(?P<duration>.+))?$"
)
_YEAR_RANGE_RE = re.compile(r"^(?P<start>\d{4})\s*[-–—]\s*(?P<end>\d{4}|Present|present)$")


@dataclass
class ParsedProfile:
    identity: Identity | None = None
    about: str | None = None
    experiences: list[Experience] | None = None
    education: list[Education] | None = None
    skills: list[Skill] | None = None
    certifications: list[Certification] | None = None
    languages: list[Language] | None = None
    warnings: list[str] = field(default_factory=list)


def _strip_bullet(line: str) -> str | None:
    stripped = line.lstrip()
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return None


def _parse_month_year(token: str) -> DatePart | None:
    token = token.strip()
    match = re.match(r"^([A-Za-z]{3,9})\s+(\d{4})$", token)
    if match:
        month = _MONTHS.get(match.group(1)[:3].lower())
        return DatePart(year=int(match.group(2)), month=month)
    match = re.match(r"^(\d{4})$", token)
    if match:
        return DatePart(year=int(match.group(1)))
    return None


def _parse_date_range(line: str) -> tuple[DatePart | None, DatePart | None, bool] | None:
    match = _DATE_RANGE_RE.match(line.strip())
    if not match:
        return None
    start = _parse_month_year(match.group("start"))
    end_token = match.group("end")
    is_present = end_token.lower() == "present"
    end = None if is_present else _parse_month_year(end_token)
    return start, end, is_present


def _split_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def _split_sections(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    heading_positions: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        key = line.strip().lower()
        if key in KNOWN_HEADINGS:
            heading_positions.append((i, KNOWN_HEADINGS[key]))

    header_lines = lines[: heading_positions[0][0]] if heading_positions else lines
    sections: dict[str, list[str]] = {}
    for idx, (start_i, name) in enumerate(heading_positions):
        end_i = heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        sections.setdefault(name, []).extend(lines[start_i + 1 : end_i])
    return header_lines, sections


def _split_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def _dedupe_adjacent(lines: list[str]) -> list[str]:
    """Collapses LinkedIn's occasional duplicated company/title lines."""
    out: list[str] = []
    for line in lines:
        if out and out[-1] == line:
            continue
        out.append(line)
    return out


def _resplit_block_by_dates(block: list[str]) -> list[list[str]]:
    """A blank-line block sometimes holds several grouped roles at one
    company (no blank line between them) — resplit at each date-range
    line, attributing up to two preceding lines as that entry's header."""
    date_positions = [i for i, line in enumerate(block) if _DATE_RANGE_RE.match(line)]
    if len(date_positions) <= 1:
        return [block]

    sub_blocks: list[list[str]] = []
    prev_end = 0
    for i, pos in enumerate(date_positions):
        header_start = max(prev_end, pos - 2)
        next_pos = date_positions[i + 1] if i + 1 < len(date_positions) else len(block)
        entry_end = max(pos + 1, next_pos - 2)
        sub_blocks.append(block[header_start:entry_end])
        prev_end = entry_end
    return sub_blocks


def _strip_employment_type(line: str) -> tuple[str, str | None]:
    if "·" in line:
        left, _, right = line.rpartition("·")
        right = right.strip()
        if right in EMPLOYMENT_TYPES:
            return left.strip(" ·"), right
    return line, None


def _parse_experience_block(block: list[str], warnings: list[str]) -> Experience:
    block = _dedupe_adjacent(block)
    date_idx = next((i for i, line in enumerate(block) if _DATE_RANGE_RE.match(line)), None)

    if date_idx is None:
        warnings.append(
            "Could not find a date range in an experience entry; kept the raw "
            f"text as its description: {' | '.join(block)[:120]}"
        )
        return Experience(description="\n".join(block))

    header_lines = block[:date_idx]
    title: str | None = None
    company: str | None = None
    employment_type: str | None = None

    if len(header_lines) >= 2:
        title = header_lines[0]
        company, employment_type = _strip_employment_type(header_lines[1])
    elif len(header_lines) == 1:
        title = header_lines[0]
        warnings.append(
            f"Experience entry {title!r} had no separate company line before its date range."
        )
    else:
        warnings.append("An experience entry's date range had no title/company above it.")

    parsed_dates = _parse_date_range(block[date_idx])
    start, end, is_current = parsed_dates if parsed_dates else (None, None, False)

    location: str | None = None
    description_lines: list[str] = []
    bullets: list[str] = []
    for line in block[date_idx + 1 :]:
        bullet_text = _strip_bullet(line)
        if bullet_text is not None:
            bullets.append(bullet_text)
        elif location is None and "," in line and len(line) < 100:
            location = line
        else:
            description_lines.append(line)

    return Experience(
        company=company or None,
        title=title,
        employment_type=employment_type,
        location=location,
        start=start,
        end=end,
        is_current=is_current,
        description="\n".join(description_lines) if description_lines else None,
        bullets=bullets or None,
    )


def _parse_experience_section(lines: list[str], warnings: list[str]) -> list[Experience]:
    experiences: list[Experience] = []
    for block in _split_blocks(lines):
        for sub_block in _resplit_block_by_dates(block):
            if sub_block:
                experiences.append(_parse_experience_block(sub_block, warnings))
    return experiences


def _parse_education_block(block: list[str], warnings: list[str]) -> Education:
    block = _dedupe_adjacent(block)
    if not block:
        return Education()

    school = block[0]
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    description_lines: list[str] = []

    rest = block[1:]
    year_line_idx = next((i for i, line in enumerate(rest) if _YEAR_RANGE_RE.match(line)), None)

    if len(rest) >= 1 and (year_line_idx is None or year_line_idx != 0):
        degree_line = rest[0]
        if "," in degree_line:
            degree, _, field_of_study = (part.strip() for part in degree_line.partition(","))
        else:
            degree = degree_line

    if year_line_idx is not None:
        match = _YEAR_RANGE_RE.match(rest[year_line_idx])
        if match:
            start_year = int(match.group("start"))
            end_token = match.group("end")
            end_year = None if end_token.lower() == "present" else int(end_token)
        description_lines = rest[year_line_idx + 1 :]
    elif len(rest) > 1:
        description_lines = rest[1:]

    if not degree and not year_line_idx:
        warnings.append(f"Could not confidently parse an education entry for {school!r}.")

    return Education(
        school=school,
        degree=degree,
        field=field_of_study,
        start_year=start_year,
        end_year=end_year,
        description="\n".join(description_lines) if description_lines else None,
    )


def _parse_skill_line(line: str) -> Skill:
    match = re.match(r"^(.*?)\s*·\s*(\d+)\s+endorsements?$", line, re.IGNORECASE)
    if match:
        return Skill(name=match.group(1).strip(), endorsements=int(match.group(2)))
    return Skill(name=line.strip())


def _parse_certification_block(block: list[str]) -> Certification:
    block = _dedupe_adjacent(block)
    name = block[0] if block else None
    issuer = block[1] if len(block) > 1 else None
    issued: DatePart | None = None
    credential_id: str | None = None
    url: str | None = None

    for line in block[2:]:
        issued_match = re.match(r"^Issued\s+(.+)$", line, re.IGNORECASE)
        credential_match = re.match(r"^Credential ID\s+(.+)$", line, re.IGNORECASE)
        if issued_match:
            issued = _parse_month_year(issued_match.group(1).split("·")[0].strip())
        elif credential_match:
            credential_id = credential_match.group(1).strip()
        elif line.startswith("http"):
            url = line.strip()

    return Certification(
        name=name, issuer=issuer, issued=issued, credential_id=credential_id, url=url
    )


def _parse_language_block(block: list[str]) -> Language:
    if len(block) >= 2:
        return Language(name=block[0], proficiency=block[1])
    if block and " - " in block[0]:
        name, _, proficiency = block[0].partition(" - ")
        return Language(name=name.strip(), proficiency=proficiency.strip())
    return Language(name=block[0] if block else None)


def _parse_header(header_lines: list[str], warnings: list[str]) -> Identity | None:
    non_empty = [line.strip() for line in header_lines if line.strip()]
    if not non_empty:
        return None

    full_name = non_empty[0]
    headline = non_empty[1] if len(non_empty) > 1 else None
    location = next((line for line in non_empty[2:] if "," in line and len(line) < 100), None)
    return Identity(full_name=full_name, headline=headline, location=location)


def parse_paste(text: str) -> ParsedProfile:
    """Parses a pasted profile text block. Never raises on malformed
    input — anything it can't confidently segment becomes a warning."""
    warnings: list[str] = []
    lines = _split_lines(text)
    header_lines, sections = _split_sections(lines)

    identity = _parse_header(header_lines, warnings)

    about_lines = [line for line in sections.get("about", []) if line.strip()]
    about = "\n".join(about_lines) if about_lines else None

    experiences = (
        _parse_experience_section(sections["experience"], warnings)
        if "experience" in sections
        else None
    )
    education = (
        [_parse_education_block(b, warnings) for b in _split_blocks(sections["education"])]
        if "education" in sections
        else None
    )
    skills = (
        [_parse_skill_line(line) for line in sections["skills"] if line.strip()]
        if "skills" in sections
        else None
    )
    certifications = (
        [_parse_certification_block(b) for b in _split_blocks(sections["certifications"])]
        if "certifications" in sections
        else None
    )
    languages = (
        [_parse_language_block(b) for b in _split_blocks(sections["languages"])]
        if "languages" in sections
        else None
    )

    if not sections:
        warnings.append(
            "No recognised section headings (About, Experience, Education, "
            "Skills, ...) were found in the pasted text."
        )

    return ParsedProfile(
        identity=identity,
        about=about,
        experiences=experiences,
        education=education,
        skills=skills,
        certifications=certifications,
        languages=languages,
        warnings=warnings,
    )


def parsed_profile_to_snapshot(parsed: ParsedProfile, *, source: ProfileSource) -> ProfileSnapshot:
    """Wraps a ParsedProfile into a ProfileSnapshot with field_provenance
    recorded per top-level section that was actually populated."""
    confidence_by_field = {
        "identity": 0.7,
        "about": 0.75,
        "experiences": 0.6,
        "education": 0.65,
        "skills": 0.8,
        "certifications": 0.65,
        "languages": 0.75,
    }
    provenance: dict[str, FieldProvenance] = {}
    for field_name, confidence in confidence_by_field.items():
        if getattr(parsed, field_name):
            provenance[f"/{field_name}"] = FieldProvenance(source=source, confidence=confidence)

    return ProfileSnapshot(
        source=source,
        captured_at=datetime.now(UTC),
        identity=parsed.identity,
        about=parsed.about,
        experiences=parsed.experiences,
        education=parsed.education,
        skills=parsed.skills,
        certifications=parsed.certifications,
        languages=parsed.languages,
        field_provenance=provenance,
    )
