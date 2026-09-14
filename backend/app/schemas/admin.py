from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    plan: str
    role: str
    status: str
    created_at: datetime
    last_login_at: datetime | None


class AdminUserSearchResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int


class AdminSubscriptionSummary(BaseModel):
    provider: str
    plan: str
    status: str
    current_period_end: datetime | None


class AdminToolRunSummary(BaseModel):
    id: str
    tool_id: str
    status: str
    created_at: datetime


class AdminUserDetailResponse(BaseModel):
    user: AdminUserResponse
    subscription: AdminSubscriptionSummary | None
    recent_tool_runs: list[AdminToolRunSummary]
    ai_spend_minor_this_month: int
    ai_run_count_this_month: int


class SuspendUserRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class AdjustPlanRequest(BaseModel):
    plan: str
    reason: str = Field(min_length=1, max_length=2000)


class ForcePasswordResetResponse(BaseModel):
    reset_token: str


class ImpersonateResponse(BaseModel):
    access_token: str
    expires_at: datetime


class AdminSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    provider: str
    plan: str
    status: str
    current_period_end: datetime | None
    cancel_at_period_end: bool


class WebhookEventResponse(BaseModel):
    id: str
    provider: str
    provider_event_id: str
    type: str
    status: str
    attempts: int
    received_at: datetime
    processed_at: datetime | None
    error: str | None


class FeatureFlagResponse(BaseModel):
    key: str
    enabled_globally: bool
    rollout_percent: int
    description: str | None


class SetFlagGlobalRequest(BaseModel):
    enabled_globally: bool


class SetFlagRolloutRequest(BaseModel):
    rollout_percent: int = Field(ge=0, le=100)


class SetFlagUserOverrideRequest(BaseModel):
    user_id: str
    enabled: bool | None


class CostByDayResponse(BaseModel):
    day: date
    cost_minor: int
    tokens_in: int
    tokens_out: int
    invocation_count: int


class CostByDimensionResponse(BaseModel):
    key: str
    cost_minor: int
    invocation_count: int


class OutcomeRatesResponse(BaseModel):
    total: int
    invalid_output_rate: float
    fallback_rate: float
    policy_blocked_rate: float
    provider_error_rate: float


class SlowPromptResponse(BaseModel):
    prompt_id: str
    avg_latency_ms: float
    p95_latency_ms: float
    invocation_count: int


class AiOpsOverviewResponse(BaseModel):
    cost_by_day: list[CostByDayResponse]
    cost_by_model: list[CostByDimensionResponse]
    cost_by_prompt: list[CostByDimensionResponse]
    outcome_rates: OutcomeRatesResponse
    slowest_prompts: list[SlowPromptResponse]


class AiInvocationResponse(BaseModel):
    id: str
    user_id: str
    prompt_id: str
    prompt_version: int
    tier: str
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_minor: int
    latency_ms: int
    cached: bool
    fallback_used: bool
    outcome: str
    created_at: datetime


class ModerationFlagResponse(BaseModel):
    id: str
    user_id: str
    source: str
    target_type: str
    target_id: str
    reason: str
    excerpt: str
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime


class ReviewFlagRequest(BaseModel):
    status: str
    note: str | None = None


class QueueDepthResponse(BaseModel):
    queued: int
    leased: int
    dead: int
    failed_last_hour: int


class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    attempts: int
    error: str | None
    created_at: datetime
    finished_at: datetime | None


class PlatformHealthResponse(BaseModel):
    queue_depth: QueueDepthResponse
    dead_jobs: list[JobResponse]
    circuit_breakers: dict[str, dict[str, Any]]
