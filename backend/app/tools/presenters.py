"""Model -> response-schema mapping for everything the tools router
returns: a tool's own definition, a persisted run, a saved asset, and a
quota snapshot."""

from __future__ import annotations

from app.billing.quota import QuotaStatus
from app.models.asset import Asset
from app.models.tool_run import ToolRun
from app.schemas.tools import (
    AssetResponse,
    QuotaInfo,
    ToolRunResponse,
    ToolRunSummary,
    ToolSummary,
)
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
        counts_as_outreach=definition.counts_as_outreach,
    )


def to_quota_info(quota: QuotaStatus) -> QuotaInfo:
    return QuotaInfo(metric=quota.metric, used=quota.used, limit=quota.limit)


def to_tool_run_response(
    run: ToolRun, *, quota: QuotaStatus, warning: str | None = None
) -> ToolRunResponse:
    assert run.output is not None  # a "failed" run never reaches this presenter
    return ToolRunResponse(
        run_id=str(run.id),
        output=run.output,
        context_used=list(run.context_keys),
        quota=to_quota_info(quota),
        warning=warning,
    )


def to_tool_run_summary(run: ToolRun) -> ToolRunSummary:
    return ToolRunSummary(
        id=str(run.id),
        tool_id=run.tool_id,
        input=run.input,
        output=run.output,
        context_used=list(run.context_keys),
        status=run.status,
        rating=run.rating,
        feedback_text=run.feedback_text,
        parent_run_id=str(run.parent_run_id) if run.parent_run_id else None,
        created_at=run.created_at,
    )


def to_asset_response(asset: Asset) -> AssetResponse:
    return AssetResponse(
        id=str(asset.id),
        type=asset.type,
        title=asset.title,
        body=asset.body,
        body_format=asset.body_format,
        source_tool_run_id=str(asset.source_tool_run_id) if asset.source_tool_run_id else None,
        folder_id=str(asset.folder_id) if asset.folder_id else None,
        metadata=asset.metadata_,
        created_at=asset.created_at,
    )
