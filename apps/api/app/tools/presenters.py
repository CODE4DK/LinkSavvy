"""ToolDefinition -> response-schema mapping, shared by the tools list
and (once a tool is selected) anywhere else that needs to describe a
tool on the wire."""

from __future__ import annotations

from app.schemas.tools import ToolSummary
from app.tools.definition import ToolDefinition


def to_tool_summary(definition: ToolDefinition) -> ToolSummary:
    return ToolSummary(
        id=definition.id,
        hub=definition.hub.value,
        name=definition.name,
        short_description=definition.short_description,
        input_schema=definition.input_schema.model_json_schema(),
        output_schema=definition.output_schema.model_json_schema(),
        required_context=[key.value for key in definition.required_context],
        optional_context=[key.value for key in definition.optional_context],
        min_plan=definition.min_plan.value,
        quota_metric=definition.quota_metric,
        result_renderer=definition.result_renderer.value,
        save_as=definition.save_as.value if definition.save_as else None,
        free_daily_cap=definition.free_daily_cap,
        supports_streaming=definition.supports_streaming,
    )
