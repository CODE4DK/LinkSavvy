"""The Tool Framework's public API. See app/tools/ for the definition
shape, the registry that discovers and validates tools, and the
context assembler every tool's prompt is built from. This router is a
thin HTTP translation layer over app/tools/service.py -- nothing here
is specific to any one tool.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.user import User
from app.schemas.tools import (
    AssetResponse,
    RateRequest,
    RateResponse,
    RegenerateRequest,
    SaveAssetRequest,
    ToolRunRequest,
    ToolRunResponse,
    ToolRunSummary,
    ToolSummary,
)
from app.tools import service
from app.tools.definition import Hub
from app.tools.presenters import (
    to_asset_response,
    to_tool_run_response,
    to_tool_run_summary,
    to_tool_summary,
)
from app.tools.registry import get_registry, get_tool

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("", response_model=list[ToolSummary])
async def list_tools(
    hub: Hub | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ToolSummary]:
    registry = get_registry()
    definitions = registry.by_hub(hub) if hub is not None else registry.all()
    definitions = await service.visible_tools(db, user=user, definitions=definitions)
    return [to_tool_summary(definition) for definition in definitions]


async def _sse_events(frames: AsyncIterator[dict[str, Any]]) -> AsyncIterator[str]:
    async for frame in frames:
        yield f"data: {json.dumps(frame)}\n\n"


@router.post("/{tool_id}/run", response_model=None)
async def run_tool(
    tool_id: str,
    payload: ToolRunRequest,
    stream: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ToolRunResponse | StreamingResponse:
    if stream:
        definition, input_data = await service.prepare_tool_run(
            db, user=user, tool_id=tool_id, raw_input=payload.input
        )
        frames = service.stream_tool_run(
            db, user=user, definition=definition, input_data=input_data
        )
        return StreamingResponse(_sse_events(frames), media_type="text/event-stream")

    run, quota, warning = await service.run_tool(
        db, user=user, tool_id=tool_id, raw_input=payload.input
    )
    return to_tool_run_response(run, quota=quota, warning=warning)


@router.get("/{tool_id}/runs", response_model=list[ToolRunSummary])
async def list_tool_runs(
    tool_id: str,
    cursor: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ToolRunSummary]:
    get_tool(tool_id)  # 404s on an unknown tool before we bother listing anything
    runs = await service.list_runs(db, user_id=user.id, tool_id=tool_id, cursor=cursor, limit=limit)
    return [to_tool_run_summary(run) for run in runs]


@router.get("/runs/{run_id}", response_model=ToolRunSummary)
async def get_tool_run(
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ToolRunSummary:
    """Single-run fetch -- the Workspace Hub's detail drawer uses this
    to show which tool produced a saved asset, with what inputs, so
    "open in tool" can re-run it."""
    run = await service.get_run_for_user(db, run_id=run_id, user_id=user.id)
    if run is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such tool run")
    return to_tool_run_summary(run)


@router.post("/runs/{run_id}/regenerate", response_model=ToolRunResponse)
async def regenerate_tool_run(
    run_id: uuid.UUID,
    payload: RegenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ToolRunResponse:
    run, quota, warning = await service.regenerate_run(
        db, user=user, run_id=run_id, nudge=payload.nudge
    )
    return to_tool_run_response(run, quota=quota, warning=warning)


@router.post("/runs/{run_id}/rate", response_model=RateResponse)
async def rate_tool_run(
    run_id: uuid.UUID,
    payload: RateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RateResponse:
    run = await service.rate_run(
        db, user=user, run_id=run_id, rating=payload.rating, feedback_text=payload.feedback_text
    )
    return RateResponse(run_id=str(run.id), rating=payload.rating, feedback_text=run.feedback_text)


@router.post("/runs/{run_id}/save", response_model=AssetResponse)
async def save_tool_run(
    run_id: uuid.UUID,
    payload: SaveAssetRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    asset = await service.save_run_as_asset(
        db,
        user=user,
        run_id=run_id,
        title=payload.title,
        body=payload.body,
        folder_id=payload.folder_id,
    )
    return to_asset_response(asset)
