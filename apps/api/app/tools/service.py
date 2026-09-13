"""The tool-run lifecycle: validate input against a tool's own schema,
gate on plan and quota, assemble context, call the gateway, persist the
result -- then regenerate, rate, save, and list runs against that same
persisted record. `app/routers/tools.py` is a thin HTTP translation
layer over this module; nothing here is specific to any one tool.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.ai.prompts.loader import get_prompt
from app.billing.quota import QuotaStatus, check_and_reserve, peek, release
from app.errors import ApiError, ErrorCode
from app.models.ai_invocation import AIInvocation
from app.models.asset import Asset
from app.models.tool_run import ToolRun
from app.models.user import User
from app.tools.context import ContextKey, ContextUnavailable, assemble
from app.tools.definition import ToolDefinition
from app.tools.registry import get_tool

# A generous default -- individual tools don't tune this today, but the
# assembler will still drop low-priority optional context rather than
# blow a provider's real context window if a profile is unusually large.
CONTEXT_TOKEN_BUDGET = 4000

_PLAN_RANK: dict[str, int] = {"free": 0, "pro": 1}

# Input field names that map straight onto a context key a tool can
# declare as required/optional -- a generic, name-based convention
# every tool's input schema can opt into, not a per-tool special case.
_EXTRA_CONTEXT_FIELDS: dict[str, ContextKey] = {
    "target_role": ContextKey.TARGET_ROLE,
    "user_supplied_text": ContextKey.USER_SUPPLIED_TEXT,
}


class AssetNotSupported(ApiError):
    def __init__(self, tool_id: str) -> None:
        super().__init__(
            ErrorCode.VALIDATION_FAILED, f"tool {tool_id!r} doesn't produce a saveable result"
        )


def _validate_plan(user: User, definition: ToolDefinition) -> None:
    if _PLAN_RANK.get(user.plan, 0) < _PLAN_RANK[definition.min_plan.value]:
        raise ApiError(
            ErrorCode.FORBIDDEN,
            f"{definition.name} requires the {definition.min_plan.value} plan",
            details={"min_plan": definition.min_plan.value, "upgrade_required": True},
        )


async def _check_free_daily_cap(
    db: AsyncSession, *, user: User, definition: ToolDefinition
) -> None:
    if definition.free_daily_cap is None or user.plan != "free":
        return
    since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    count = (
        await db.execute(
            select(func.count())
            .select_from(ToolRun)
            .where(
                ToolRun.user_id == user.id,
                ToolRun.tool_id == definition.id,
                ToolRun.created_at >= since,
            )
        )
    ).scalar_one()
    if count >= definition.free_daily_cap:
        raise ApiError(
            ErrorCode.RATE_LIMITED,
            f"You've used {definition.name} {definition.free_daily_cap} times today "
            "-- try again tomorrow, or upgrade for a higher daily limit.",
            details={
                "tool_id": definition.id,
                "free_daily_cap": definition.free_daily_cap,
                "upgrade_required": True,
            },
        )


def _validate_input(definition: ToolDefinition, input_data: dict[str, Any]) -> dict[str, Any]:
    try:
        validated = definition.input_schema.model_validate(input_data)
    except ValidationError as exc:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED,
            f"invalid input for {definition.id}",
            details={"errors": exc.errors(include_url=False, include_context=False)},
        ) from exc
    return validated.model_dump(mode="json")


def _extra_context(input_data: dict[str, Any]) -> dict[ContextKey, str]:
    extra: dict[ContextKey, str] = {}
    for field, key in _EXTRA_CONTEXT_FIELDS.items():
        value = input_data.get(field)
        if isinstance(value, str) and value.strip():
            extra[key] = value
    return extra


async def _run_and_persist(
    db: AsyncSession,
    *,
    user: User,
    definition: ToolDefinition,
    input_data: dict[str, Any],
    nudge: str | None,
    parent_run_id: uuid.UUID | None,
) -> tuple[ToolRun, QuotaStatus]:
    reservation = await check_and_reserve(db, user=user, metric=definition.quota_metric)

    try:
        context, included = await assemble(
            user=user,
            db=db,
            required=definition.required_context,
            optional=definition.optional_context,
            token_budget=CONTEXT_TOKEN_BUDGET,
            extra=_extra_context(input_data),
        )
    except ContextUnavailable:
        await release(db, reservation)
        raise

    if nudge:
        context["regeneration_nudge"] = f"## Additional instruction for this regeneration\n{nudge}"
    else:
        context["regeneration_nudge"] = ""

    started = time.monotonic()
    template = get_prompt(definition.prompt_id)
    try:
        result = await gateway.run(definition.prompt_id, context, user=user, db=db)
    except ApiError as exc:
        await release(db, reservation)
        db.add(
            ToolRun(
                user_id=user.id,
                tool_id=definition.id,
                prompt_id=definition.prompt_id,
                prompt_version=template.version,
                input=input_data,
                output=None,
                context_keys=[key.value for key in included],
                status="failed",
                duration_ms=round((time.monotonic() - started) * 1000),
                error=exc.message,
                parent_run_id=parent_run_id,
            )
        )
        await db.commit()
        raise

    assert result.parsed is not None  # every tool prompt declares a JSON output_schema
    run = ToolRun(
        user_id=user.id,
        tool_id=definition.id,
        prompt_id=definition.prompt_id,
        prompt_version=template.version,
        input=input_data,
        output=result.parsed,
        context_keys=[key.value for key in included],
        ai_invocation_id=result.invocation_id,
        status="succeeded",
        duration_ms=round((time.monotonic() - started) * 1000),
        parent_run_id=parent_run_id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    quota = await peek(db, user=user, metric=definition.quota_metric)
    return run, quota


async def prepare_tool_run(
    db: AsyncSession, *, user: User, tool_id: str, raw_input: dict[str, Any]
) -> tuple[ToolDefinition, dict[str, Any]]:
    """Everything that must succeed as an ordinary HTTP error *before* a
    streaming response's headers go out -- plan gating, the free-tier
    daily cap, and input validation all belong here, run once by both
    `run_tool` and the router's `?stream=true` path."""
    definition = get_tool(tool_id)
    _validate_plan(user, definition)
    await _check_free_daily_cap(db, user=user, definition=definition)
    input_data = _validate_input(definition, raw_input)
    return definition, input_data


async def run_tool(
    db: AsyncSession, *, user: User, tool_id: str, raw_input: dict[str, Any]
) -> tuple[ToolRun, QuotaStatus]:
    definition, input_data = await prepare_tool_run(
        db, user=user, tool_id=tool_id, raw_input=raw_input
    )
    return await _run_and_persist(
        db, user=user, definition=definition, input_data=input_data, nudge=None, parent_run_id=None
    )


async def _stream_and_persist(
    db: AsyncSession,
    *,
    user: User,
    definition: ToolDefinition,
    input_data: dict[str, Any],
) -> AsyncIterator[dict[str, Any]]:
    """Mirrors `_run_and_persist` for `?stream=true`: frames pass straight
    through from the gateway as they arrive, and the ToolRun is persisted
    only once the stream ends -- there's no partial-output record. Errors
    surface as a `type: error` frame rather than a raised exception, since
    by the time this generator runs the response's SSE headers are already
    on the wire (see `prepare_tool_run` for the checks that still raise
    normally, before streaming starts)."""
    reservation = await check_and_reserve(db, user=user, metric=definition.quota_metric)

    try:
        context, included = await assemble(
            user=user,
            db=db,
            required=definition.required_context,
            optional=definition.optional_context,
            token_budget=CONTEXT_TOKEN_BUDGET,
            extra=_extra_context(input_data),
        )
    except ContextUnavailable as exc:
        await release(db, reservation)
        yield {"type": "error", "code": exc.code.value, "message": exc.message}
        return

    context["regeneration_nudge"] = ""

    started = time.monotonic()
    template = get_prompt(definition.prompt_id)

    text_parts: list[str] = []
    correlation_id: str | None = None
    error_frame: dict[str, Any] | None = None

    async for frame in gateway.run(definition.prompt_id, context, user=user, db=db, stream=True):
        if frame["type"] == "meta":
            correlation_id = frame.get("correlation_id")
        elif frame["type"] == "delta":
            text_parts.append(frame["text"])
        elif frame["type"] == "error":
            error_frame = frame
        yield frame

    duration_ms = round((time.monotonic() - started) * 1000)

    if error_frame is not None:
        # The gateway already released or never took its own "ai_runs"
        # reservation on this path -- only our tool-level reservation
        # needs giving back here.
        await release(db, reservation)
        db.add(
            ToolRun(
                user_id=user.id,
                tool_id=definition.id,
                prompt_id=definition.prompt_id,
                prompt_version=template.version,
                input=input_data,
                output=None,
                context_keys=[key.value for key in included],
                status="failed",
                duration_ms=duration_ms,
                error=error_frame.get("message"),
            )
        )
        await db.commit()
        return

    try:
        parsed = json.loads("".join(text_parts))
    except json.JSONDecodeError:
        parsed = None

    invocation_id: uuid.UUID | None = None
    if correlation_id is not None:
        invocation = (
            await db.execute(
                select(AIInvocation).where(AIInvocation.correlation_id == correlation_id)
            )
        ).scalar_one_or_none()
        if invocation is not None:
            invocation_id = invocation.id

    run = ToolRun(
        user_id=user.id,
        tool_id=definition.id,
        prompt_id=definition.prompt_id,
        prompt_version=template.version,
        input=input_data,
        output=parsed,
        context_keys=[key.value for key in included],
        ai_invocation_id=invocation_id,
        status="succeeded",
        duration_ms=duration_ms,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    quota = await peek(db, user=user, metric=definition.quota_metric)
    yield {
        "type": "tool_run",
        "run_id": str(run.id),
        "context_used": [key.value for key in included],
        "quota": {"metric": quota.metric, "used": quota.used, "limit": quota.limit},
    }


def stream_tool_run(
    db: AsyncSession, *, user: User, definition: ToolDefinition, input_data: dict[str, Any]
) -> AsyncIterator[dict[str, Any]]:
    return _stream_and_persist(db, user=user, definition=definition, input_data=input_data)


async def get_run_for_user(
    db: AsyncSession, *, run_id: uuid.UUID, user_id: uuid.UUID
) -> ToolRun | None:
    run = await db.get(ToolRun, run_id)
    if run is None or run.user_id != user_id:
        return None
    return run


async def regenerate_run(
    db: AsyncSession, *, user: User, run_id: uuid.UUID, nudge: str | None
) -> tuple[ToolRun, QuotaStatus]:
    parent = await get_run_for_user(db, run_id=run_id, user_id=user.id)
    if parent is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such tool run")

    definition = get_tool(parent.tool_id)
    _validate_plan(user, definition)
    await _check_free_daily_cap(db, user=user, definition=definition)
    return await _run_and_persist(
        db,
        user=user,
        definition=definition,
        input_data=parent.input,
        nudge=nudge,
        parent_run_id=parent.id,
    )


async def rate_run(
    db: AsyncSession,
    *,
    user: User,
    run_id: uuid.UUID,
    rating: str,
    feedback_text: str | None,
) -> ToolRun:
    run = await get_run_for_user(db, run_id=run_id, user_id=user.id)
    if run is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such tool run")
    run.rating = rating
    run.feedback_text = feedback_text
    await db.commit()
    await db.refresh(run)
    return run


async def save_run_as_asset(
    db: AsyncSession,
    *,
    user: User,
    run_id: uuid.UUID,
    title: str,
    body: str,
    folder_id: uuid.UUID | None,
) -> Asset:
    run = await get_run_for_user(db, run_id=run_id, user_id=user.id)
    if run is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such tool run")

    definition = get_tool(run.tool_id)
    if definition.save_as is None:
        raise AssetNotSupported(definition.id)

    asset = Asset(
        user_id=user.id,
        type=definition.save_as.value,
        title=title,
        body=body,
        body_format="text",
        source_tool_run_id=run.id,
        folder_id=folder_id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def list_runs(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    tool_id: str,
    cursor: datetime | None,
    limit: int,
) -> list[ToolRun]:
    stmt = select(ToolRun).where(ToolRun.user_id == user_id, ToolRun.tool_id == tool_id)
    if cursor is not None:
        stmt = stmt.where(ToolRun.created_at < cursor)
    stmt = stmt.order_by(ToolRun.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
