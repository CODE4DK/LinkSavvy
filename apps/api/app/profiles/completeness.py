"""Deterministic completeness scoring for a ProfileSnapshot.

Weights, sections, and user-facing copy live in
`config/completeness_rules.yaml`; the boolean predicate for each rule
lives here in `CHECKS`, keyed by the rule's `code`. Given the same
snapshot and the same rules file, `compute_completeness` always returns
the same score — no randomness, no wall-clock dependence, no network
calls. Phase 3's audit/scoring work builds on top of this; it does not
replace it.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from app.profiles.schema import Experience, ProfileSnapshot

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[2] / "config" / "completeness_rules.yaml"

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _headline_present_and_substantial(snapshot: ProfileSnapshot) -> bool:
    headline = snapshot.identity.headline if snapshot.identity else None
    if not headline:
        return False
    return len(headline) > 40


def _about_present_and_substantial(snapshot: ProfileSnapshot) -> bool:
    about = snapshot.about
    if not about or not about.strip():
        return False
    sentences = [part for part in _SENTENCE_BOUNDARY.split(about.strip()) if part]
    return len(sentences) >= 3


def _has_minimum_experiences(snapshot: ProfileSnapshot) -> bool:
    if not snapshot.experiences:
        return False
    return len(snapshot.experiences) >= 2


def _current_experience(snapshot: ProfileSnapshot) -> Experience | None:
    if not snapshot.experiences:
        return None
    for experience in snapshot.experiences:
        if experience.is_current:
            return experience
    return None


def _current_role_has_detailed_description(snapshot: ProfileSnapshot) -> bool:
    current = _current_experience(snapshot)
    if current is None or not current.bullets:
        return False
    return len(current.bullets) >= 3


def _has_minimum_skills(snapshot: ProfileSnapshot) -> bool:
    if not snapshot.skills:
        return False
    return len(snapshot.skills) >= 10


def _has_certification_or_project(snapshot: ProfileSnapshot) -> bool:
    return bool(snapshot.certifications) or bool(snapshot.projects)


def _has_custom_url(snapshot: ProfileSnapshot) -> bool:
    return bool(snapshot.identity and snapshot.identity.custom_url)


def _has_profile_photo(snapshot: ProfileSnapshot) -> bool:
    return bool(snapshot.identity and snapshot.identity.profile_picture_url)


CHECKS: dict[str, Callable[[ProfileSnapshot], bool]] = {
    "headline_present_and_substantial": _headline_present_and_substantial,
    "about_present_and_substantial": _about_present_and_substantial,
    "has_minimum_experiences": _has_minimum_experiences,
    "current_role_has_detailed_description": _current_role_has_detailed_description,
    "has_minimum_skills": _has_minimum_skills,
    "has_certification_or_project": _has_certification_or_project,
    "has_custom_url": _has_custom_url,
    "has_profile_photo": _has_profile_photo,
}


@dataclass(frozen=True)
class CompletenessRule:
    code: str
    section: str
    weight: int
    severity: str
    message: str
    fix_hint: str


@dataclass(frozen=True)
class CompletenessGap:
    code: str
    section: str
    severity: str
    message: str
    fix_hint: str


@dataclass(frozen=True)
class SectionBreakdown:
    earned: int
    possible: int

    @property
    def score(self) -> int:
        if self.possible == 0:
            return 0
        return round(100 * self.earned / self.possible)


@dataclass(frozen=True)
class CompletenessResult:
    score: int
    section_breakdown: dict[str, SectionBreakdown] = field(default_factory=dict)
    gaps: list[CompletenessGap] = field(default_factory=list)


@lru_cache(maxsize=8)
def _load_rules(rules_path: str) -> tuple[CompletenessRule, ...]:
    raw = yaml.safe_load(Path(rules_path).read_text())
    rules = tuple(CompletenessRule(**entry) for entry in raw["rules"])
    unknown = [rule.code for rule in rules if rule.code not in CHECKS]
    if unknown:
        raise ValueError(f"completeness_rules.yaml references unknown check(s): {unknown}")
    return rules


def compute_completeness(
    snapshot: ProfileSnapshot, *, rules_path: Path = DEFAULT_RULES_PATH
) -> CompletenessResult:
    rules = _load_rules(str(rules_path))

    total_weight = sum(rule.weight for rule in rules)
    earned_weight = 0
    gaps: list[CompletenessGap] = []
    section_totals: dict[str, list[int]] = {}  # section -> [earned, possible]

    for rule in rules:
        passed = CHECKS[rule.code](snapshot)
        earned, possible = section_totals.setdefault(rule.section, [0, 0])
        section_totals[rule.section][1] = possible + rule.weight
        if passed:
            earned_weight += rule.weight
            section_totals[rule.section][0] = earned + rule.weight
        else:
            gaps.append(
                CompletenessGap(
                    code=rule.code,
                    section=rule.section,
                    severity=rule.severity,
                    message=rule.message,
                    fix_hint=rule.fix_hint,
                )
            )

    score = round(100 * earned_weight / total_weight) if total_weight else 0
    breakdown = {
        section: SectionBreakdown(earned=values[0], possible=values[1])
        for section, values in section_totals.items()
    }
    return CompletenessResult(score=score, section_breakdown=breakdown, gaps=gaps)
