from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ToolSummary(BaseModel):
    """One row of `GET /api/v1/tools` -- everything the web app needs to
    render a tool card and, on selection, a fully working form and
    result view with no tool-specific frontend code."""

    model_config = ConfigDict(extra="forbid")

    id: str
    hub: str
    name: str
    short_description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    required_context: list[str]
    optional_context: list[str]
    min_plan: str
    quota_metric: str
    result_renderer: str
    save_as: str | None
    free_daily_cap: int | None
    supports_streaming: bool


class ToolRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: dict[str, Any]


class QuotaInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    used: int
    limit: int


class ToolRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    output: dict[str, Any]
    context_used: list[str]
    quota: QuotaInfo


class ToolRunSummary(BaseModel):
    """One row of `GET /api/v1/tools/{id}/runs`."""

    model_config = ConfigDict(extra="forbid")

    id: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    context_used: list[str]
    status: str
    rating: str | None
    feedback_text: str | None
    parent_run_id: str | None
    created_at: datetime


class RegenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nudge: str | None = None


class RateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: Literal["up", "down"]
    feedback_text: str | None = None


class RateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    rating: str
    feedback_text: str | None


class SaveAssetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str
    folder_id: uuid.UUID | None = None


class AssetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    title: str
    body: str
    body_format: str
    source_tool_run_id: str | None
    folder_id: str | None
    metadata: dict[str, Any]
    created_at: datetime
