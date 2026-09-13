from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.ai.prompts.models import PromptTemplate
from app.ai.providers.base import ModelTier
from app.models.user import User
from app.tools.registry import ToolRegistry

_DEFINITION_SOURCE = """
from pydantic import BaseModel
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _Input(BaseModel):
    text: str
    user_supplied_text: str = ""


class _Output(BaseModel):
    text: str


DEFINITION = ToolDefinition(
    id="{tool_id}",
    hub={hub},
    name="Fixture Tool",
    short_description="A tool for router tests.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="fixture.tool.v1",
    required_context=[ContextKey.USER_SUPPLIED_TEXT],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as=AssetType.ANALYSIS,
)
"""


class _Output(BaseModel):
    text: str


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


@pytest.fixture
def fixture_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ToolRegistry:
    (tmp_path / "profile_tool.py").write_text(
        _DEFINITION_SOURCE.format(tool_id="profile.fixture", hub="Hub.PROFILE")
    )
    (tmp_path / "content_tool.py").write_text(
        _DEFINITION_SOURCE.format(tool_id="content.fixture", hub="Hub.CONTENT")
    )

    def _fake_get_prompt(prompt_id: str) -> PromptTemplate:
        return PromptTemplate(
            id=prompt_id,
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
    monkeypatch.setattr("app.routers.tools.get_registry", lambda: registry)
    # `get_tool()` (used by the run/regenerate/rate/save/history endpoints,
    # via app/tools/service.py) is defined in app.tools.registry and looks
    # up `get_registry` in that module's own namespace at call time, so
    # patching it here also covers every caller that imported `get_tool`
    # by reference -- unlike `get_registry` itself, which each importer
    # binds at import time and so needs patching per-module (above).
    monkeypatch.setattr("app.tools.registry.get_registry", lambda: registry)
    return registry


def _patch_gateway_success(
    monkeypatch: pytest.MonkeyPatch, *, output_text: str = "generated"
) -> None:
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


async def test_list_tools_returns_json_schema_for_input_and_output(
    client: AsyncClient, registered_user: dict[str, str], fixture_registry: ToolRegistry
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.get("/api/v1/tools", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert {tool["id"] for tool in body} == {"profile.fixture", "content.fixture"}
    profile_tool = next(tool for tool in body if tool["id"] == "profile.fixture")
    assert profile_tool["hub"] == "profile"
    assert profile_tool["input_schema"]["properties"]["text"]["type"] == "string"
    assert profile_tool["output_schema"]["properties"]["text"]["type"] == "string"
    assert profile_tool["required_context"] == ["user_supplied_text"]
    assert profile_tool["result_renderer"] == "document"


async def test_list_tools_filters_by_hub(
    client: AsyncClient, registered_user: dict[str, str], fixture_registry: ToolRegistry
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.get(
        "/api/v1/tools?hub=content", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert [tool["id"] for tool in body] == ["content.fixture"]


async def test_list_tools_requires_auth(
    client: AsyncClient, fixture_registry: ToolRegistry
) -> None:
    response = await client.get("/api/v1/tools")
    assert response.status_code == 401


async def test_run_tool_returns_output_and_quota(
    client: AsyncClient,
    registered_user: dict[str, str],
    fixture_registry: ToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_gateway_success(monkeypatch)
    token = await _access_token(client, registered_user)
    response = await client.post(
        "/api/v1/tools/profile.fixture/run",
        json={"input": {"text": "ignored", "user_supplied_text": "hello there"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["output"] == {"text": "generated"}
    assert body["context_used"] == ["user_supplied_text"]
    assert body["quota"]["metric"] == "tool_runs"
    assert body["quota"]["used"] == 1
    assert uuid.UUID(body["run_id"])


async def test_run_tool_returns_422_for_invalid_input(
    client: AsyncClient,
    registered_user: dict[str, str],
    fixture_registry: ToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_gateway_success(monkeypatch)
    token = await _access_token(client, registered_user)
    response = await client.post(
        "/api/v1/tools/profile.fixture/run",
        json={"input": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_run_tool_returns_404_for_unknown_tool(
    client: AsyncClient,
    registered_user: dict[str, str],
    fixture_registry: ToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_gateway_success(monkeypatch)
    token = await _access_token(client, registered_user)
    response = await client.post(
        "/api/v1/tools/no.such.tool/run",
        json={"input": {"text": "x", "user_supplied_text": "hi"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


async def test_run_tool_streams_sse_frames_and_a_final_tool_run_frame(
    client: AsyncClient,
    registered_user: dict[str, str],
    fixture_registry: ToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_stream(
        prompt_id: str, context: dict[str, Any], *, user: User, db: AsyncSession, **kwargs: Any
    ) -> Any:
        yield {
            "type": "meta",
            "correlation_id": "corr-stream-1",
            "model": "fake-model",
            "provider": "fake",
            "cached": False,
        }
        yield {"type": "delta", "text": '{"text": '}
        yield {"type": "delta", "text": '"streamed"}'}
        yield {"type": "done", "tokens_in": 5, "tokens_out": 5, "cost_minor": 0}

    def _fake_run(
        prompt_id: str,
        context: dict[str, Any],
        *,
        user: User,
        db: AsyncSession,
        tier_override: Any = None,
        stream: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        return _fake_stream(prompt_id, context, user=user, db=db)

    monkeypatch.setattr(gateway, "run", _fake_run)
    token = await _access_token(client, registered_user)

    async with client.stream(
        "POST",
        "/api/v1/tools/profile.fixture/run?stream=true",
        json={"input": {"text": "ignored", "user_supplied_text": "hello"}},
        headers={"Authorization": f"Bearer {token}"},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        raw = b""
        async for chunk in response.aiter_bytes():
            raw += chunk

    lines = [line for line in raw.decode().split("\n\n") if line.strip()]
    frames = [json.loads(line.removeprefix("data: ")) for line in lines]
    types = [frame["type"] for frame in frames]
    assert types == ["meta", "delta", "delta", "done", "tool_run"]
    final = frames[-1]
    assert final["context_used"] == ["user_supplied_text"]
    assert final["quota"]["metric"] == "tool_runs"
    assert uuid.UUID(final["run_id"])


async def test_regenerate_and_rate_and_save_and_history(
    client: AsyncClient,
    registered_user: dict[str, str],
    fixture_registry: ToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_gateway_success(monkeypatch)
    token = await _access_token(client, registered_user)
    headers = {"Authorization": f"Bearer {token}"}

    run_response = await client.post(
        "/api/v1/tools/profile.fixture/run",
        json={"input": {"text": "ignored", "user_supplied_text": "hello"}},
        headers=headers,
    )
    run_id = run_response.json()["run_id"]

    _patch_gateway_success(monkeypatch, output_text="shorter")
    regenerate_response = await client.post(
        f"/api/v1/tools/runs/{run_id}/regenerate",
        json={"nudge": "make it shorter"},
        headers=headers,
    )
    assert regenerate_response.status_code == 200
    assert regenerate_response.json()["output"] == {"text": "shorter"}
    child_run_id = regenerate_response.json()["run_id"]
    assert child_run_id != run_id

    rate_response = await client.post(
        f"/api/v1/tools/runs/{run_id}/rate",
        json={"rating": "up", "feedback_text": "nice"},
        headers=headers,
    )
    assert rate_response.status_code == 200
    assert rate_response.json() == {"run_id": run_id, "rating": "up", "feedback_text": "nice"}

    save_response = await client.post(
        f"/api/v1/tools/runs/{run_id}/save",
        json={"title": "My saved output", "body": "generated"},
        headers=headers,
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["type"] == "analysis"
    assert saved["title"] == "My saved output"
    assert saved["source_tool_run_id"] == run_id

    history_response = await client.get("/api/v1/tools/profile.fixture/runs", headers=headers)
    assert history_response.status_code == 200
    history = history_response.json()
    assert {run["id"] for run in history} == {run_id, child_run_id}


async def test_rate_and_regenerate_return_404_for_a_run_that_doesnt_exist(
    client: AsyncClient,
    registered_user: dict[str, str],
    fixture_registry: ToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = await _access_token(client, registered_user)
    headers = {"Authorization": f"Bearer {token}"}
    missing_run_id = str(uuid.uuid4())

    rate_response = await client.post(
        f"/api/v1/tools/runs/{missing_run_id}/rate",
        json={"rating": "up"},
        headers=headers,
    )
    assert rate_response.status_code == 404

    regenerate_response = await client.post(
        f"/api/v1/tools/runs/{missing_run_id}/regenerate", json={}, headers=headers
    )
    assert regenerate_response.status_code == 404
