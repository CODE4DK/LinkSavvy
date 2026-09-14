from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GatewayMetricsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    window_hours: int
    total_invocations: int
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    cache_hit_rate: float | None
    fallback_rate: float | None
    invalid_output_rate: float | None
    cost_per_user_per_day_minor: dict[str, int]
