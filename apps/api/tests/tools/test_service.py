"""Unit tests for app/tools/service.py -- the tool-run lifecycle: plan
gating, the free-tier daily cap, context assembly failures, and the
regenerate/rate/save/list operations against a persisted ToolRun. The
AI gateway itself is faked here (see `_patch_gateway`) so these tests
exercise the framework's own logic, not a prompt or a provider -- that
coverage belongs to each tool's own golden test (Section 5).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.ai.prompts.models import PromptTemplate
from app.ai.providers.base import ModelTier
from app.errors import ApiError, ErrorCode
from app.models.user import User
from app.tools import service
from app.tools.context import ContextUnavailable
from app.tools.registry import ToolRegistry

_DEFINITION_SOURCE = """
from pydantic import BaseModel
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, Plan, ResultRenderer, ToolDefinition


class _Input(BaseModel):
    user_supplied_text: str


class _Output(BaseModel):
    text: str


DEFINITION = ToolDefinition(
    id="{tool_id}",
    hub=Hub.PROFILE,
    name="Fixture Tool",
    short_description="A tool for service tests.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="{prompt_id}",
    required_context=[ContextKey.USER_SUPPLIED_TEXT],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as={save_as},
    quota_metric="tool_runs",
    min_plan=Plan.{min_plan},
    free_daily_cap={free_daily_cap!r},
    counts_as_outreach={counts_as_outreach!r},
)
"""


class _Output(BaseModel):
    text: str


def _build_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    tool_id: str = "fixture.tool",
    prompt_id: str = "fixture.tool.v1",
    min_plan: str = "FREE",
    free_daily_cap: int | None = None,
    save_as: str = "AssetType.ANALYSIS",
    counts_as_outreach: bool = False,
) -> ToolRegistry:
    (tmp_path / "fixture_tool.py").write_text(
        _DEFINITION_SOURCE.format(
            tool_id=tool_id,
            prompt_id=prompt_id,
            min_plan=min_plan,
            free_daily_cap=free_daily_cap,
            save_as=save_as,
            counts_as_outreach=counts_as_outreach,
        )
    )

    def _fake_get_prompt(requested_id: str) -> PromptTemplate:
        return PromptTemplate(
            id=requested_id,
            version=1,
            tier=ModelTier.FAST,
            output_schema=_Output.model_json_schema(),
            max_output_tokens=100,
            temperature=0.5,
            cache_ttl_seconds=0,
            description="fixture",
        )

    monkeypatch.setattr("app.tools.registry.get_prompt", _fake_get_prompt)
    monkeypatch.setattr("app.tools.service.get_prompt", _fake_get_prompt)
    registry = ToolRegistry(definitions_dir=tmp_path)
    monkeypatch.setattr("app.tools.registry.get_registry", lambda: registry)
    return registry


def _patch_gateway_success(monkeypatch: pytest.MonkeyPatch, *, output_text: str = "echoed") -> None:
    async def _fake_run(
        prompt_id: str,
        context: dict[str, Any],
        *,
        user: User,
        db: AsyncSession,
        tier_override: Any = None,
        idempotency_key: str | None = None,
    ) -> gateway.GatewayResult:
        return gateway.GatewayResult(
            text=f'{{"text": "{output_text}"}}',
            parsed={"text": output_text},
            model="fake-model",
            provider="fake",
            tokens_in=5,
            tokens_out=5,
            cost_minor=0,
            currency="USD",
            latency_ms=1.0,
            cached=False,
            fallback_used=False,
            correlation_id="corr-1",
            invocation_id=uuid.uuid4(),
        )

    monkeypatch.setattr(gateway, "run", _fake_run)


def _patch_gateway_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_run(*args: Any, **kwargs: Any) -> gateway.GatewayResult:
        raise gateway.AIProviderUnavailable("fixture.tool.v1")

    monkeypatch.setattr(gateway, "run", _fake_run)


async def _get_user(db: AsyncSession, email: str) -> User:
    return (await db.execute(select(User).where(User.email == email))).scalar_one()


async def test_run_tool_persists_a_succeeded_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])

    run, quota, _ = await service.run_tool(
        db_session,
        user=user,
        tool_id="fixture.tool",
        raw_input={"user_supplied_text": "hello"},
    )

    assert run.status == "succeeded"
    assert run.output == {"text": "echoed"}
    assert run.context_keys == ["user_supplied_text"]
    assert run.prompt_version == 1
    assert quota.metric == "tool_runs"
    assert quota.used == 1


async def test_run_tool_rejects_input_that_fails_the_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])

    with pytest.raises(ApiError) as exc_info:
        await service.run_tool(db_session, user=user, tool_id="fixture.tool", raw_input={})
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED


async def test_run_tool_raises_context_unavailable_for_missing_required_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])

    with pytest.raises(ContextUnavailable):
        await service.run_tool(
            db_session,
            user=user,
            tool_id="fixture.tool",
            raw_input={"user_supplied_text": "   "},
        )


async def test_run_tool_gates_on_min_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch, min_plan="PRO")
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])

    with pytest.raises(ApiError) as exc_info:
        await service.run_tool(
            db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
        )
    assert exc_info.value.code == ErrorCode.FORBIDDEN
    assert exc_info.value.details["upgrade_required"] is True


async def test_run_tool_enforces_free_daily_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch, free_daily_cap=1)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])

    await service.run_tool(
        db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "one"}
    )
    with pytest.raises(ApiError) as exc_info:
        await service.run_tool(
            db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "two"}
        )
    assert exc_info.value.code == ErrorCode.RATE_LIMITED


async def test_run_tool_warns_past_the_outreach_soft_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    from app.engagement.guardrails import OUTREACH_DAILY_SOFT_CAP

    _build_registry(tmp_path, monkeypatch, counts_as_outreach=True)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])
    user.plan = "pro"  # the free plan's own tool_runs quota (15/day) would
    # otherwise block before the soft cap is even reached
    await db_session.commit()

    warning = None
    for _ in range(OUTREACH_DAILY_SOFT_CAP + 1):
        _, _, warning = await service.run_tool(
            db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
        )
    assert warning is not None
    assert "quality" in warning.lower()


async def test_run_tool_does_not_warn_for_a_non_outreach_tool(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    from app.engagement.guardrails import OUTREACH_DAILY_SOFT_CAP

    _build_registry(tmp_path, monkeypatch, counts_as_outreach=False)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])
    user.plan = "pro"
    await db_session.commit()

    warning = None
    for _ in range(OUTREACH_DAILY_SOFT_CAP + 1):
        _, _, warning = await service.run_tool(
            db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
        )
    assert warning is None


async def test_run_tool_records_a_failed_run_and_reraises_on_gateway_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_failure(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])

    with pytest.raises(gateway.AIProviderUnavailable):
        await service.run_tool(
            db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
        )

    runs = await service.list_runs(
        db_session, user_id=user.id, tool_id="fixture.tool", cursor=None, limit=10
    )
    assert len(runs) == 1
    assert runs[0].status == "failed"
    assert runs[0].output is None


async def test_regenerate_run_creates_a_child_run_with_the_nudge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])

    parent, _, _ = await service.run_tool(
        db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
    )

    seen_nudge: dict[str, str] = {}

    async def _fake_run(
        prompt_id: str, context: dict[str, Any], *, user: User, db: AsyncSession, **kwargs: Any
    ) -> gateway.GatewayResult:
        seen_nudge["value"] = context["regeneration_nudge"]
        return gateway.GatewayResult(
            text='{"text": "shorter"}',
            parsed={"text": "shorter"},
            model="fake-model",
            provider="fake",
            tokens_in=5,
            tokens_out=5,
            cost_minor=0,
            currency="USD",
            latency_ms=1.0,
            cached=False,
            fallback_used=False,
            correlation_id="corr-2",
            invocation_id=uuid.uuid4(),
        )

    monkeypatch.setattr(gateway, "run", _fake_run)

    child, _, _ = await service.regenerate_run(
        db_session, user=user, run_id=parent.id, nudge="make it shorter"
    )

    assert child.parent_run_id == parent.id
    assert child.output == {"text": "shorter"}
    assert "make it shorter" in seen_nudge["value"]


async def test_regenerate_run_raises_not_found_for_a_nonexistent_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_success(monkeypatch)

    with pytest.raises(ApiError) as exc_info:
        await service.regenerate_run(
            db_session,
            user=await _get_user(db_session, registered_user["email"]),
            run_id=uuid.uuid4(),
            nudge=None,
        )
    assert exc_info.value.code == ErrorCode.NOT_FOUND


async def test_rate_run_stores_rating_and_feedback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])
    run, _, _ = await service.run_tool(
        db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
    )

    rated = await service.rate_run(
        db_session, user=user, run_id=run.id, rating="up", feedback_text="great"
    )
    assert rated.rating == "up"
    assert rated.feedback_text == "great"


async def test_save_run_as_asset_creates_an_asset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch)
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])
    run, _, _ = await service.run_tool(
        db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
    )

    asset = await service.save_run_as_asset(
        db_session, user=user, run_id=run.id, title="My asset", body="echoed", folder_id=None
    )
    assert asset.type == "analysis"
    assert asset.title == "My asset"
    assert asset.source_tool_run_id == run.id


async def test_save_run_as_asset_rejects_a_tool_with_no_save_as(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user: dict[str, str],
) -> None:
    _build_registry(tmp_path, monkeypatch, save_as="None")
    _patch_gateway_success(monkeypatch)
    user = await _get_user(db_session, registered_user["email"])
    run, _, _ = await service.run_tool(
        db_session, user=user, tool_id="fixture.tool", raw_input={"user_supplied_text": "hi"}
    )

    with pytest.raises(service.AssetNotSupported):
        await service.save_run_as_asset(
            db_session, user=user, run_id=run.id, title="x", body="y", folder_id=None
        )
