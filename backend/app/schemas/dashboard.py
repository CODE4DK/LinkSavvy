from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.audit import (
    AuditCategoryResultResponse,
    RecommendationResponse,
    ScoreHistoryPoint,
)

RunAuditBlockedReason = Literal[
    "no_active_snapshot", "audit_in_progress", "cooldown_active", "quota_exceeded"
]


class DashboardUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    plan: str


class DashboardHealthScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    overall: int | None
    scoring_version: str
    status: str
    completed_at: datetime | None
    categories: list[AuditCategoryResultResponse]


class DashboardRunAuditState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    can_run: bool
    reason: RunAuditBlockedReason | None
    retry_after_seconds: int | None
    in_flight_job_id: str | None
    quota_used: int
    quota_limit: int


class DashboardScoreHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    range: str
    points: list[ScoreHistoryPoint]
    # Overall-score delta between the earliest and latest point in range,
    # None when there are fewer than two points to compare.
    delta: int | None


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: DashboardUser
    # True when no audit has ever completed for this user -- drives the
    # dashboard's first-time empty state instead of an empty health score.
    is_first_time: bool
    health_score: DashboardHealthScore | None
    score_history: DashboardScoreHistory
    top_recommendations: list[RecommendationResponse]
    run_audit: DashboardRunAuditState
    hubs: dict[str, bool]
