from __future__ import annotations

from typing import Any

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
