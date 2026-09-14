"""Deterministic (rule-based) resume checks -- run before, and clearly
labelled apart from, `career.resume_analyzer`'s AI pass. These never
call the gateway; they're plain regex/heuristics over the resume text
the tool was given, so the user can tell exactly which findings are
objective fact and which are the AI's judgement (see
app/tools/definitions/career/resume_analyzer.py's postprocess, which
merges this module's findings into the AI's own).
"""

from __future__ import annotations

import re
from typing import Any, TypedDict

_WEAK_VERBS = [
    "responsible for",
    "duties included",
    "helped with",
    "worked on",
    "involved in",
    "assisted with",
    "in charge of",
]
_BULLET_RE = re.compile(r"^\s*[•‣●◦▪\-*]\s+", re.MULTILINE)
_METRIC_RE = re.compile(r"\d")
_DATE_RANGE_RE = re.compile(
    r"[A-Za-z]{3,9}\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4}\s*[-–—]\s*(?:present|current|\d{4})",
    re.IGNORECASE,
)

_MIN_WORDS = 250
_MAX_WORDS = 900


class Finding(TypedDict):
    title: str
    severity: str
    description: str
    recommendation: str
    rule_based: bool


def _finding(title: str, severity: str, description: str, recommendation: str) -> Finding:
    return {
        "title": title,
        "severity": severity,
        "description": description,
        "recommendation": recommendation,
        "rule_based": True,
    }


def check_length(text: str) -> Finding | None:
    word_count = len(text.split())
    if word_count < _MIN_WORDS:
        return _finding(
            "Resume may be too short",
            "warning",
            f"This resume is about {word_count} words -- shorter than most reviewers expect "
            "for anyone with more than a couple of years of experience.",
            "Add more detail to your most recent, most relevant roles.",
        )
    if word_count > _MAX_WORDS:
        return _finding(
            "Resume may be too long",
            "info",
            f"This resume is about {word_count} words -- long enough that a reviewer "
            "skimming it in 10 seconds may miss your best material.",
            "Cut older or less relevant roles down to their most impactful lines.",
        )
    return None


def check_bullet_count(text: str) -> Finding | None:
    bullet_count = len(_BULLET_RE.findall(text))
    if bullet_count == 0:
        return _finding(
            "No bullet points detected",
            "warning",
            "This resume doesn't appear to use bullet points for accomplishments.",
            "Break experience descriptions into concise, scannable bullets.",
        )
    return None


def check_weak_verbs(text: str) -> Finding | None:
    lowered = text.lower()
    found = [verb for verb in _WEAK_VERBS if verb in lowered]
    if found:
        return _finding(
            "Weak, passive bullet openers found",
            "warning",
            f"Found {len(found)} phrase(s) that describe duties rather than impact: "
            f"{', '.join(sorted(found))}.",
            "Replace with a strong action verb and, where possible, the result it produced.",
        )
    return None


def check_metrics(text: str) -> Finding | None:
    bullets = _BULLET_RE.split(text)[1:]
    if not bullets:
        return None
    with_metrics = sum(1 for bullet in bullets if _METRIC_RE.search(bullet))
    ratio = with_metrics / len(bullets)
    if ratio < 0.3:
        return _finding(
            "Most bullets have no quantified result",
            "warning",
            f"Only {with_metrics} of {len(bullets)} bullets contain a number.",
            "Quantify impact where you can (%, $, time saved, team size, scale).",
        )
    return None


def check_date_gaps(text: str) -> Finding | None:
    ranges = _DATE_RANGE_RE.findall(text)
    if len(ranges) < 2:
        return None
    years: list[int] = []
    for match in re.finditer(r"\d{4}", " ".join(ranges)):
        years.append(int(match.group(0)))
    if len(years) < 2:
        return None
    years.sort()
    for earlier, later in zip(years, years[1:], strict=False):
        if later - earlier > 1:
            return _finding(
                "Possible gap between roles",
                "info",
                f"There's more than a year between {earlier} and {later} in the dates found.",
                "If there's an employment gap, consider a brief note explaining it "
                "(sabbatical, education, caregiving) rather than leaving it unexplained.",
            )
    return None


def run_deterministic_checks(text: str) -> list[Finding]:
    checks = (check_length, check_bullet_count, check_weak_verbs, check_metrics, check_date_gaps)
    findings: list[Finding] = []
    for check in checks:
        result = check(text)
        if result is not None:
            findings.append(result)
    return findings


def analyzer_postprocess(output: dict[str, Any], raw_input: dict[str, Any]) -> dict[str, Any]:
    resume_text = str(raw_input.get("resume_text", ""))
    ai_findings = output.get("findings", [])
    deterministic = run_deterministic_checks(resume_text)
    return {**output, "findings": [*deterministic, *ai_findings]}
