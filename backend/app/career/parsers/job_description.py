"""Deterministic parsing of a pasted or uploaded job description into
`JobDescriptionRequirements` -- the structure Resume<->JD Match and ATS
Optimization score a resume against. Unlike the resume pipeline this
never calls the AI gateway: a job posting's own structure (headed
sections, a seniority word in the title, a stated location/work mode)
is regular enough to read out directly.
"""

from __future__ import annotations

import re

from app.career.schema import JobDescriptionRequirements

_RESPONSIBILITY_HEADINGS = {"responsibilities", "what you'll do"}
_REQUIRED_HEADINGS = {"requirements", "required qualifications", "what you'll need", "must haves"}
_PREFERRED_HEADINGS = {"preferred qualifications", "nice to have", "bonus points", "preferred"}

_SENIORITY_KEYWORDS = [
    ("principal", "principal"),
    ("staff", "staff"),
    ("senior", "senior"),
    ("sr.", "senior"),
    ("lead", "lead"),
    ("junior", "junior"),
    ("jr.", "junior"),
    ("entry level", "entry level"),
    ("director", "director"),
    ("vp", "vp"),
    ("vice president", "vp"),
    ("manager", "manager"),
]

_WORK_MODE_KEYWORDS = [
    ("fully remote", "remote"),
    ("remote", "remote"),
    ("hybrid", "hybrid"),
    ("on-site", "onsite"),
    ("onsite", "onsite"),
    ("in-office", "onsite"),
]

_LOCATION_RE = re.compile(r"\b([A-Z][a-zA-Z.]+(?:\s[A-Z][a-zA-Z.]+)*,\s*[A-Z]{2})\b")
_BULLET_PREFIXES = ("•", "‣", "●", "◦", "▪", "- ", "* ")

_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "you",
    "your",
    "our",
    "will",
    "have",
    "are",
    "this",
    "that",
    "from",
    "who",
    "into",
    "than",
    "they",
    "them",
    "able",
    "team",
    "work",
    "role",
    "years",
    "year",
    "experience",
}
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z+./#-]{2,}")


def _strip_bullet(line: str) -> str:
    stripped = line.lstrip()
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return stripped


def _split_sections(text: str) -> dict[str, list[str]]:
    lines = [line.strip() for line in text.splitlines()]
    all_headings = _RESPONSIBILITY_HEADINGS | _REQUIRED_HEADINGS | _PREFERRED_HEADINGS
    heading_positions = [
        (i, line.strip().lower().strip(":"))
        for i, line in enumerate(lines)
        if line.strip().lower().strip(":") in all_headings
    ]
    sections: dict[str, list[str]] = {}
    for idx, (start_i, name) in enumerate(heading_positions):
        end_i = heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        sections.setdefault(name, []).extend(line for line in lines[start_i + 1 : end_i] if line)
    return sections


def _detect_seniority(text: str) -> str | None:
    lowered = text.lower()
    for keyword, label in _SENIORITY_KEYWORDS:
        if keyword in lowered:
            return label
    return None


def _detect_work_mode(text: str) -> str | None:
    lowered = text.lower()
    for keyword, label in _WORK_MODE_KEYWORDS:
        if keyword in lowered:
            return label
    return None


def _detect_location(text: str) -> str | None:
    match = _LOCATION_RE.search(text)
    return match.group(1) if match else None


def _extract_keywords(text: str, *, limit: int = 25) -> list[str]:
    counts: dict[str, int] = {}
    for word in _WORD_RE.findall(text):
        lowered = word.lower()
        if lowered in _STOPWORDS or len(lowered) < 3:
            continue
        counts[lowered] = counts.get(lowered, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:limit]]


def parse_job_description(text: str) -> JobDescriptionRequirements:
    sections = _split_sections(text)

    responsibilities = [
        _strip_bullet(line)
        for heading in _RESPONSIBILITY_HEADINGS
        for line in sections.get(heading, [])
    ]
    required_qualifications = [
        _strip_bullet(line) for heading in _REQUIRED_HEADINGS for line in sections.get(heading, [])
    ]
    preferred_qualifications = [
        _strip_bullet(line) for heading in _PREFERRED_HEADINGS for line in sections.get(heading, [])
    ]

    # Keywords are drawn from the structured requirement/responsibility
    # lines, not the whole posting -- narrative filler ("we're looking
    # for", "about the role") would otherwise crowd out the specific
    # skills a match/ATS check actually needs to see.
    keyword_source = "\n".join(
        responsibilities + required_qualifications + preferred_qualifications
    )

    return JobDescriptionRequirements(
        responsibilities=responsibilities,
        required_qualifications=required_qualifications,
        preferred_qualifications=preferred_qualifications,
        keywords=_extract_keywords(keyword_source or text),
        seniority=_detect_seniority(text),
        location=_detect_location(text),
        work_mode=_detect_work_mode(text),
    )
