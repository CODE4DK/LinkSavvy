from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.prompts.loader import PromptRegistry, validate_required_context
from app.ai.prompts.models import (
    PromptContextError,
    PromptError,
    PromptNotFound,
    PromptVersionMismatch,
)
from app.ai.prompts.render import PromptRenderError, render_prompt
from app.ai.providers.base import ModelTier

_VALID_FRONTMATTER = """\
---
id: test.greeting
version: 1
tier: fast
output_schema: text
max_output_tokens: 200
temperature: 0.5
cache_ttl_seconds: 60
description: Says hello.
required_context:
  - name
---
Say hello to {{ name }}.
"""


def _write(dir_: Path, filename: str, content: str) -> Path:
    path = dir_ / filename
    path.write_text(content)
    return path


def test_valid_prompt_loads_with_expected_fields(tmp_path: Path) -> None:
    _write(tmp_path, "test.greeting.prompt.md", _VALID_FRONTMATTER)
    registry = PromptRegistry(tmp_path)
    template = registry.get("test.greeting")
    assert template.version == 1
    assert template.tier == ModelTier.FAST
    assert template.output_schema is None
    assert template.max_output_tokens == 200
    assert template.temperature == 0.5
    assert template.cache_ttl_seconds == 60
    assert template.required_context == ["name"]
    assert template.body_hash  # non-empty sha256 hex digest


def test_output_schema_path_is_loaded_and_validated(tmp_path: Path) -> None:
    schema = {
        "type": "object",
        "properties": {"greeting": {"type": "string"}},
        "required": ["greeting"],
    }
    (tmp_path / "greeting.schema.json").write_text(json.dumps(schema))
    _write(
        tmp_path,
        "test.greeting.prompt.md",
        _VALID_FRONTMATTER.replace("output_schema: text", "output_schema: greeting.schema.json"),
    )
    registry = PromptRegistry(tmp_path)
    template = registry.get("test.greeting")
    assert template.output_schema == schema


def test_invalid_json_schema_fails_fast(tmp_path: Path) -> None:
    (tmp_path / "greeting.schema.json").write_text(json.dumps({"type": "not-a-real-type"}))
    _write(
        tmp_path,
        "test.greeting.prompt.md",
        _VALID_FRONTMATTER.replace("output_schema: text", "output_schema: greeting.schema.json"),
    )
    with pytest.raises(PromptError, match="not a valid JSON Schema"):
        PromptRegistry(tmp_path)


def test_missing_frontmatter_key_fails_fast(tmp_path: Path) -> None:
    broken = _VALID_FRONTMATTER.replace("temperature: 0.5\n", "")
    _write(tmp_path, "test.greeting.prompt.md", broken)
    with pytest.raises(PromptError, match="missing required key"):
        PromptRegistry(tmp_path)


def test_filename_must_match_id(tmp_path: Path) -> None:
    _write(tmp_path, "wrong-name.prompt.md", _VALID_FRONTMATTER)
    with pytest.raises(PromptError, match="filename must match its id"):
        PromptRegistry(tmp_path)


def test_second_file_claiming_the_same_id_fails_the_filename_check(tmp_path: Path) -> None:
    # The filename<->id bijection means a true "duplicate id" can only
    # arise as a filename mismatch on the second file — this confirms the
    # loader still fails fast rather than silently picking one.
    _write(tmp_path, "test.greeting.prompt.md", _VALID_FRONTMATTER)
    _write(tmp_path, "test.greeting.copy.prompt.md", _VALID_FRONTMATTER)
    with pytest.raises(PromptError, match="filename must match its id"):
        PromptRegistry(tmp_path)


def test_empty_directory_fails_fast(tmp_path: Path) -> None:
    with pytest.raises(PromptError, match="no prompt files found"):
        PromptRegistry(tmp_path)


def test_get_prompt_not_found(tmp_path: Path) -> None:
    _write(tmp_path, "test.greeting.prompt.md", _VALID_FRONTMATTER)
    registry = PromptRegistry(tmp_path)
    with pytest.raises(PromptNotFound):
        registry.get("no.such.prompt")


def test_get_prompt_version_pin_mismatch_raises(tmp_path: Path) -> None:
    _write(tmp_path, "test.greeting.prompt.md", _VALID_FRONTMATTER)
    registry = PromptRegistry(tmp_path)
    registry.get("test.greeting", version=1)  # matches, no error
    with pytest.raises(PromptVersionMismatch):
        registry.get("test.greeting", version=2)


def test_validate_required_context_reports_missing_keys(tmp_path: Path) -> None:
    _write(tmp_path, "test.greeting.prompt.md", _VALID_FRONTMATTER)
    template = PromptRegistry(tmp_path).get("test.greeting")
    with pytest.raises(PromptContextError, match="name"):
        validate_required_context(template, {})
    validate_required_context(template, {"name": "Ada"})  # no error


def test_render_prompt_substitutes_flat_variables(tmp_path: Path) -> None:
    _write(tmp_path, "test.greeting.prompt.md", _VALID_FRONTMATTER)
    template = PromptRegistry(tmp_path).get("test.greeting")
    assert render_prompt(template, {"name": "Ada"}) == "Say hello to Ada."


def test_render_prompt_blocks_attribute_access(tmp_path: Path) -> None:
    template_source = _VALID_FRONTMATTER.replace(
        "Say hello to {{ name }}.", "Say hello to {{ name.upper() }}."
    )
    _write(tmp_path, "test.greeting.prompt.md", template_source)
    template = PromptRegistry(tmp_path).get("test.greeting")
    with pytest.raises(PromptRenderError):
        render_prompt(template, {"name": "Ada"})


def test_render_prompt_blocks_item_access(tmp_path: Path) -> None:
    template_source = _VALID_FRONTMATTER.replace(
        "Say hello to {{ name }}.", "Say hello to {{ name['x'] }}."
    )
    _write(tmp_path, "test.greeting.prompt.md", template_source)
    template = PromptRegistry(tmp_path).get("test.greeting")
    with pytest.raises(PromptRenderError):
        render_prompt(template, {"name": "Ada"})


def test_render_prompt_raises_on_undefined_variable(tmp_path: Path) -> None:
    _write(tmp_path, "test.greeting.prompt.md", _VALID_FRONTMATTER)
    template = PromptRegistry(tmp_path).get("test.greeting")
    with pytest.raises(PromptRenderError):
        render_prompt(template, {})
