"""Deterministic ATS-parseability checks. Primarily deterministic by
design (per the phase spec): everything here is a plain text/structure
check, never an AI judgement call. `career.ats_optimizer`'s AI pass is
used only for natural keyword placement suggestions -- see
app/tools/definitions/career/ats_optimizer.py -- never for the findings
this module produces.
"""

from __future__ import annotations

import re
from typing import Any, TypedDict

from app.career.parsers.job_description import parse_job_description
from app.career.parsers.segment import _KNOWN_HEADINGS, _split_lines, _split_sections

_SPECIAL_CHAR_RE = re.compile(r"[‘’“”–—•●�]")
_UNSAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]")
_WORD_RE = re.compile(r"[a-z][a-z0-9+./#-]{2,}")


class Finding(TypedDict):
    title: str
    severity: str
    description: str
    recommendation: str


def _finding(title: str, severity: str, description: str, recommendation: str) -> Finding:
    return {
        "title": title,
        "severity": severity,
        "description": description,
        "recommendation": recommendation,
    }


def check_standard_headings(text: str) -> Finding | None:
    _, sections = _split_sections(_split_lines(text))
    canonical_present = {name for name in sections if not name.startswith("custom:")}
    if "experience" not in canonical_present:
        return _finding(
            'No standard "Experience" heading found',
            "critical",
            "ATS software matches section headings against a known list -- a non-standard "
            "or missing experience heading can mean your work history isn't parsed at all.",
            f"Use one of the standard headings: {', '.join(sorted(set(_KNOWN_HEADINGS.values())))}.",
        )
    return None


def check_special_characters(text: str) -> Finding | None:
    matches = _SPECIAL_CHAR_RE.findall(text)
    if matches:
        return _finding(
            "Non-standard characters found",
            "warning",
            "Smart quotes, em-dashes, or unusual bullet glyphs can render as garbage "
            "characters in some ATS parsers.",
            "Replace with plain ASCII equivalents (straight quotes, a hyphen, a plain dash).",
        )
    return None


def check_layout(*, detected_two_column_layout: bool) -> Finding | None:
    if detected_two_column_layout:
        return _finding(
            "Multi-column layout detected",
            "critical",
            "Many ATS parsers read left-to-right across the whole page, scrambling a "
            "two-column layout's content.",
            "Switch to a single-column layout for the version you submit through an ATS.",
        )
    return None


def check_file_name(file_name: str) -> Finding | None:
    if not file_name:
        return None
    stem = file_name.rsplit(".", 1)[0]
    if _UNSAFE_FILENAME_RE.search(stem):
        return _finding(
            "File name may not survive an upload pipeline",
            "info",
            f"{file_name!r} contains spaces or special characters some ATS uploaders mangle.",
            "Name the file like firstname-lastname-resume.pdf.",
        )
    return None


def check_missing_keywords(resume_text: str, job_description_text: str) -> Finding | None:
    if not job_description_text.strip():
        return None
    jd = parse_job_description(job_description_text)
    resume_words = {w.lower() for w in _WORD_RE.findall(resume_text.lower())}
    missing = [kw for kw in jd.keywords if kw not in resume_words]
    if missing:
        return _finding(
            "Job description keywords missing from this resume",
            "warning",
            f"{len(missing)} keyword(s) from the job description don't appear anywhere in "
            f"this resume: {', '.join(missing[:10])}.",
            "Work genuine keywords you actually have experience with into your bullets.",
        )
    return None


def run_ats_checks(
    *,
    resume_text: str,
    job_description_text: str,
    file_name: str,
    detected_two_column_layout: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    for finding in (
        check_standard_headings(resume_text),
        check_special_characters(resume_text),
        check_layout(detected_two_column_layout=detected_two_column_layout),
        check_file_name(file_name),
        check_missing_keywords(resume_text, job_description_text),
    ):
        if finding is not None:
            findings.append(finding)
    return findings


def ats_optimizer_postprocess(output: dict[str, Any], raw_input: dict[str, Any]) -> dict[str, Any]:
    findings = run_ats_checks(
        resume_text=str(raw_input.get("resume_text", "")),
        job_description_text=str(raw_input.get("job_description_text", "")),
        file_name=str(raw_input.get("file_name", "")),
        detected_two_column_layout=bool(raw_input.get("detected_two_column_layout", False)),
    )
    return {**output, "findings": findings}
