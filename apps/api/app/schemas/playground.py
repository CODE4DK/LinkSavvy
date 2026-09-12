from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class PlaygroundPromptSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: int
    tier: str
    description: str
    required_context: list[str]
    output_schema: dict[str, Any] | None
    max_output_tokens: int
    temperature: float
    cache_ttl_seconds: int


class PlaygroundRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_id: str
    context: dict[str, str]
    tier_override: str | None = None


class PlaygroundRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str | None
    parsed: Any | None
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    cost_minor: int
    currency: str
    latency_ms: float
    cached: bool
    fallback_used: bool
    correlation_id: str
