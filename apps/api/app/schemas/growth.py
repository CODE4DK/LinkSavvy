from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

GrowthGoalStatusLiteral = Literal["active", "completed", "abandoned"]


class ScoreComponentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    weight: int
    value: int | None
    evidence: dict[str, Any]


class GrowthScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score_type: str
    value: int | None
    status: str
    components: list[ScoreComponentResponse]
    computed_at: datetime
    scoring_version: str
    needed: dict[str, Any] | None


class GrowthScoresResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health: GrowthScoreResponse
    visibility: GrowthScoreResponse
    consistency: GrowthScoreResponse
    personal_branding: GrowthScoreResponse


class WeeklyPlanItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    why_now: str
    tool_id: str | None
    estimated_minutes: int
    expected_impact: int
    category: str
    completed: bool


class WeeklyPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    week_start: date
    generated_at: datetime
    focus: str
    items: list[WeeklyPlanItemResponse]
    status: str
    completed_count: int
    reflection: dict[str, Any] | None


class WeeklyPlanItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: bool


class GrowthGoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_type: str
    target_role: str | None = None
    target_description: str = ""
    horizon_weeks: int = Field(ge=1, le=104)


class GrowthGoalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    goal_type: str
    target_role: str | None
    target_description: str
    horizon_weeks: int
    started_at: datetime
    status: GrowthGoalStatusLiteral
    baseline_scores: dict[str, Any]


class CoachMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)


class CoachMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    role: Literal["user", "assistant"]
    content: str
    metadata: dict[str, Any]
    created_at: datetime


class CoachSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    goal_id: str | None
    started_at: datetime
    messages: list[CoachMessageResponse]
