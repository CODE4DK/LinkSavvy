"""Loads the `growth:` section of config/scoring.yaml -- the three
Growth Hub scores that aren't just the Audit Engine's overall score
(Health Score reuses app.audit.scoring's config directly instead; see
app/growth/scores/health.py). Mirrors app/audit/scoring.py's own
validation (component weights per score must sum to 100) so a
misconfigured weight fails at import time, not silently at score time.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.audit.scoring import DEFAULT_SCORING_PATH, ScoringComponent

GrowthScoreType = str  # "visibility" | "consistency" | "personal_branding"


@dataclass(frozen=True, slots=True)
class GrowthScoringConfig:
    scoring_version: str
    score_components: dict[GrowthScoreType, tuple[ScoringComponent, ...]]


@lru_cache(maxsize=1)
def load_growth_scoring_config(path: str = str(DEFAULT_SCORING_PATH)) -> GrowthScoringConfig:
    raw = yaml.safe_load(Path(path).read_text())
    growth_raw = raw["growth"]

    score_components = {
        score_type: tuple(ScoringComponent(**component) for component in data["components"])
        for score_type, data in growth_raw["scores"].items()
    }
    for score_type, components in score_components.items():
        total = sum(component.weight for component in components)
        if total != 100:
            raise ValueError(
                f"config/scoring.yaml: growth score {score_type!r} component weights "
                f"sum to {total}, not 100"
            )

    return GrowthScoringConfig(
        scoring_version=growth_raw["scoring_version"],
        score_components=score_components,
    )


def growth_component_weight(score_type: GrowthScoreType, code: str) -> int:
    config = load_growth_scoring_config()
    for component in config.score_components[score_type]:
        if component.code == code:
            return component.weight
    raise KeyError(f"no growth scoring component {code!r} registered for score {score_type!r}")
