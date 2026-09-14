"""The one envelope every Growth Hub score returns -- Health,
Visibility, Consistency, and Personal Branding all produce exactly
this shape, so the frontend's score row/chart/detail views never
special-case one score's format against another's.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GrowthScoreType(StrEnum):
    HEALTH = "health"
    VISIBILITY = "visibility"
    CONSISTENCY = "consistency"
    PERSONAL_BRANDING = "personal_branding"


class GrowthScoreStatus(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"
    SKIPPED = "skipped"


class ScoreComponent(BaseModel):
    """A score with no evidence for a component is a bug -- `evidence`
    is required (may be an empty dict only when `value` itself is
    `None`, i.e. this component couldn't be assessed at all)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    weight: int = Field(ge=0, le=100)
    value: int | None = Field(default=None, ge=0, le=100)
    evidence: dict[str, Any] = Field(default_factory=dict)


class GrowthScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score_type: GrowthScoreType
    value: int | None = Field(default=None, ge=0, le=100)
    status: GrowthScoreStatus
    components: list[ScoreComponent]
    computed_at: datetime
    scoring_version: str
    # Present only when status == insufficient_data: what's needed to
    # unlock real scoring, e.g. {"weeks_with_activity": 2, "weeks_needed": 4}.
    needed: dict[str, Any] | None = None
