from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class AuditRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_role: str | None = None
    content_history: list[str] | None = None


class AuditRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    audit_status: Literal["queued"] = "queued"


class AuditFindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: str
    code: str
    severity: str
    title: str
    evidence: dict[str, Any]
    deterministic: bool


class AuditCategoryResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    score: int | None
    status: str
    inputs_available: dict[str, Any]
    detail: dict[str, Any]
    findings: list[AuditFindingResponse]


class AuditDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: str
    scoring_version: str
    overall_score: int | None
    trigger: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error: str | None
    categories: list[AuditCategoryResultResponse]


class ScoreHistoryPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    recorded_at: datetime
    overall: int
    profile: int | None
    content: int | None
    engagement: int | None
    career: int | None
    visibility: int | None


class ScoreHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    range: str
    points: list[ScoreHistoryPoint]


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    audit_id: str
    category: str
    priority: int
    title: str
    why: str
    action_label: str
    action_route: str
    action_tool_id: str | None
    estimated_impact_points: int
    status: str
    completed_at: datetime | None


class RecommendationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RecommendationResponse]
    next_cursor: str | None


RecommendationStatusValue = Literal["open", "in_progress", "done", "dismissed"]


class RecommendationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RecommendationStatusValue
