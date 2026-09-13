from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient
from pydantic import BaseModel

from app.ai.prompts.models import PromptTemplate
from app.ai.providers.base import ModelTier
from app.tools.registry import ToolRegistry

_DEFINITION_SOURCE = """
from pydantic import BaseModel
from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _Input(BaseModel):
    text: str


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
    registry = ToolRegistry(definitions_dir=tmp_path)
    monkeypatch.setattr("app.routers.tools.get_registry", lambda: registry)
    return registry


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
