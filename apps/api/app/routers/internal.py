"""Internal, admin-only endpoints: observability and the AI developer
playground. Never proxied to the public frontend."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.ai.metrics import compute_metrics
from app.ai.prompts.loader import all_prompts
from app.ai.providers.base import ModelTier
from app.deps import get_current_admin, get_db
from app.errors import ApiError, ErrorCode
from app.models.user import User
from app.schemas.internal import GatewayMetricsResponse
from app.schemas.playground import (
    PlaygroundPromptSummary,
    PlaygroundRunRequest,
    PlaygroundRunResponse,
)
from app.services.feature_flags import resolve_flags_for_user

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/metrics", response_model=GatewayMetricsResponse)
async def get_gateway_metrics(
    window_hours: int = Query(default=24, ge=1, le=24 * 30),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GatewayMetricsResponse:
    metrics = await compute_metrics(db, window_hours=window_hours)
    return GatewayMetricsResponse(**asdict(metrics))


async def require_playground_enabled(
    admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> User:
    """Admin role alone isn't enough — the dev.playground flag (seeded on
    by migration 0004, since it's admin-gated regardless and isn't hiding
    an incomplete feature the way a hub flag would) has to be on too."""
    flags = await resolve_flags_for_user(db, user_id=admin.id)
    if not flags.get("dev.playground", False):
        raise ApiError(ErrorCode.FORBIDDEN, "The developer playground is not enabled")
    return admin


def _parse_tier_override(value: str | None) -> ModelTier | None:
    if value is None:
        return None
    try:
        return ModelTier(value)
    except ValueError as exc:
        valid = [tier.value for tier in ModelTier]
        raise ApiError(
            ErrorCode.VALIDATION_FAILED, f"tier_override must be one of {valid}"
        ) from exc


def _to_run_response(result: gateway.GatewayResult) -> PlaygroundRunResponse:
    return PlaygroundRunResponse(
        text=result.text,
        parsed=result.parsed,
        model=result.model,
        provider=result.provider,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_minor=result.cost_minor,
        currency=result.currency,
        latency_ms=result.latency_ms,
        cached=result.cached,
        fallback_used=result.fallback_used,
        correlation_id=result.correlation_id,
    )


async def _sse_events(frames: AsyncIterator[dict[str, Any]]) -> AsyncIterator[str]:
    async for frame in frames:
        yield f"data: {json.dumps(frame)}\n\n"


@router.get("/playground/prompts", response_model=list[PlaygroundPromptSummary])
async def list_playground_prompts(
    _admin: User = Depends(require_playground_enabled),
) -> list[PlaygroundPromptSummary]:
    return [
        PlaygroundPromptSummary(
            id=template.id,
            version=template.version,
            tier=template.tier.value,
            description=template.description,
            required_context=template.required_context,
            output_schema=template.output_schema,
            max_output_tokens=template.max_output_tokens,
            temperature=template.temperature,
            cache_ttl_seconds=template.cache_ttl_seconds,
        )
        for template in all_prompts()
    ]


@router.post("/playground/run", response_model=PlaygroundRunResponse)
async def run_playground_prompt(
    payload: PlaygroundRunRequest,
    admin: User = Depends(require_playground_enabled),
    db: AsyncSession = Depends(get_db),
) -> PlaygroundRunResponse:
    result = await gateway.run(
        payload.prompt_id,
        payload.context,
        user=admin,
        db=db,
        tier_override=_parse_tier_override(payload.tier_override),
    )
    return _to_run_response(result)


@router.post("/playground/stream")
async def stream_playground_prompt(
    payload: PlaygroundRunRequest,
    admin: User = Depends(require_playground_enabled),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    frames = gateway.run(
        payload.prompt_id,
        payload.context,
        user=admin,
        db=db,
        tier_override=_parse_tier_override(payload.tier_override),
        stream=True,
    )
    return StreamingResponse(_sse_events(frames), media_type="text/event-stream")
