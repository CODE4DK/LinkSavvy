from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from app.ai.prompts.models import PromptNotFound, PromptTemplate
from app.ai.providers.base import ModelTier
from app.tools.definition import Hub
from app.tools.errors import ToolDefinitionError, ToolNotFound
from app.tools.registry import ToolRegistry


# Named "_Output" to exactly match the inline class in _DEFINITION_SOURCE
# below -- model_json_schema() includes a "title" derived from the class
# name, so these must match for the registry's schema-equality check to
# treat them as the same schema.
class _Output(BaseModel):
    text: str


_DEFINITION_SOURCE = """
from pydantic import BaseModel
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _Input(BaseModel):
    text: str


class _Output(BaseModel):
    text: str


DEFINITION = ToolDefinition(
    id="{tool_id}",
    hub=Hub.PROFILE,
    name="Echo",
    short_description="Echoes back the input.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="{prompt_id}",
    result_renderer=ResultRenderer.DOCUMENT,
)
"""


def _write_definition(
    tmp_path: Path, *, tool_id: str = "test.echo", prompt_id: str = "test.echo.v1"
) -> Path:
    path = tmp_path / f"{tool_id.replace('.', '_')}.py"
    path.write_text(_DEFINITION_SOURCE.format(tool_id=tool_id, prompt_id=prompt_id))
    return path


def _make_template(*, output_schema: dict[str, Any] | None) -> PromptTemplate:
    return PromptTemplate(
        id="test.echo.v1",
        version=1,
        tier=ModelTier.FAST,
        output_schema=output_schema,
        max_output_tokens=100,
        temperature=0.5,
        cache_ttl_seconds=0,
        description="test",
    )


def test_registry_discovers_and_validates_a_matching_definition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_definition(tmp_path)
    monkeypatch.setattr(
        "app.tools.registry.get_prompt",
        lambda prompt_id: _make_template(output_schema=_Output.model_json_schema()),
    )
    registry = ToolRegistry(definitions_dir=tmp_path)
    tool = registry.get("test.echo")
    assert tool.name == "Echo"
    assert registry.all() == [tool]
    assert registry.by_hub(Hub.PROFILE) == [tool]
    assert registry.by_hub(Hub.CONTENT) == []


def test_registry_is_valid_when_empty(tmp_path: Path) -> None:
    registry = ToolRegistry(definitions_dir=tmp_path)
    assert registry.all() == []


def test_registry_rejects_definition_referencing_unknown_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_definition(tmp_path)

    def _raise(prompt_id: str) -> PromptTemplate:
        raise PromptNotFound(prompt_id)

    monkeypatch.setattr("app.tools.registry.get_prompt", _raise)
    with pytest.raises(ToolDefinitionError, match="unknown prompt"):
        ToolRegistry(definitions_dir=tmp_path)


def test_registry_rejects_a_text_only_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_definition(tmp_path)
    monkeypatch.setattr(
        "app.tools.registry.get_prompt", lambda prompt_id: _make_template(output_schema=None)
    )
    with pytest.raises(ToolDefinitionError, match="output_schema: text"):
        ToolRegistry(definitions_dir=tmp_path)


def test_registry_rejects_a_schema_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_definition(tmp_path)
    monkeypatch.setattr(
        "app.tools.registry.get_prompt",
        lambda prompt_id: _make_template(output_schema={"type": "object", "properties": {}}),
    )
    with pytest.raises(ToolDefinitionError, match="doesn't match"):
        ToolRegistry(definitions_dir=tmp_path)


def test_registry_rejects_duplicate_tool_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_definition(tmp_path, tool_id="test.echo")
    (tmp_path / "dup.py").write_text(
        _DEFINITION_SOURCE.format(tool_id="test.echo", prompt_id="test.echo.v1")
    )
    monkeypatch.setattr(
        "app.tools.registry.get_prompt",
        lambda prompt_id: _make_template(output_schema=_Output.model_json_schema()),
    )
    with pytest.raises(ToolDefinitionError, match="duplicate tool id"):
        ToolRegistry(definitions_dir=tmp_path)


def test_get_tool_raises_not_found(tmp_path: Path) -> None:
    registry = ToolRegistry(definitions_dir=tmp_path)
    with pytest.raises(ToolNotFound):
        registry.get("no.such.tool")
