"""Loads config/scoring.yaml and provides the one weighted-average
function every category, and the orchestrator's overall score, use.
Deterministic: the same inputs always produce the same score -- no
randomness, no wall-clock dependence, no network calls."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_SCORING_PATH = Path(__file__).resolve().parents[2] / "config" / "scoring.yaml"


@dataclass(frozen=True, slots=True)
class ScoringComponent:
    code: str
    weight: int
    description: str


@dataclass(frozen=True, slots=True)
class ScoringConfig:
    scoring_version: str
    category_weights: dict[str, int]
    category_components: dict[str, tuple[ScoringComponent, ...]]


@lru_cache(maxsize=1)
def load_scoring_config(path: str = str(DEFAULT_SCORING_PATH)) -> ScoringConfig:
    raw = yaml.safe_load(Path(path).read_text())

    category_components = {
        category: tuple(ScoringComponent(**component) for component in data["components"])
        for category, data in raw["categories"].items()
    }
    for category, components in category_components.items():
        total = sum(component.weight for component in components)
        if total != 100:
            raise ValueError(
                f"config/scoring.yaml: category {category!r} component weights "
                f"sum to {total}, not 100"
            )

    category_weights: dict[str, int] = raw["category_weights"]
    if sum(category_weights.values()) != 100:
        raise ValueError("config/scoring.yaml: category_weights must sum to 100")
    if set(category_weights) != set(category_components):
        raise ValueError("config/scoring.yaml: category_weights and categories keys must match")

    return ScoringConfig(
        scoring_version=raw["scoring_version"],
        category_weights=category_weights,
        category_components=category_components,
    )


def component_weight(category: str, code: str) -> int:
    config = load_scoring_config()
    for component in config.category_components[category]:
        if component.code == code:
            return component.weight
    raise KeyError(f"no scoring component {code!r} registered for category {category!r}")


def weighted_average(scores: dict[str, int | None], weights: dict[str, int]) -> int | None:
    """`scores` may map a code to `None` when that component couldn't be
    assessed (missing input, skipped sub-check) -- those are excluded and
    the remaining weights renormalized rather than treated as zero. Used
    both for a category's own component rollup and for the orchestrator's
    overall-score rollup across categories.
    """
    available = {code: score for code, score in scores.items() if score is not None}
    if not available:
        return None
    total_weight = sum(weights[code] for code in available)
    if total_weight == 0:
        return None
    weighted_sum = sum(available[code] * weights[code] for code in available)
    return round(weighted_sum / total_weight)
