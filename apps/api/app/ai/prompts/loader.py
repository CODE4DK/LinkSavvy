"""Discovers, parses, and validates every `.prompt.md` file.

Loading happens eagerly, once, the first time this module's registry is
touched — `app/main.py` imports and calls `get_registry()` at process
startup specifically so a malformed prompt fails the boot, not the first
request that happens to use it.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from jsonschema.validators import Draft202012Validator

from app.ai.prompts.models import (
    PromptContextError,
    PromptError,
    PromptNotFound,
    PromptTemplate,
    PromptVersionMismatch,
)
from app.ai.providers.base import ModelTier

DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent
FRONTMATTER_DELIMITER = "---"
_REQUIRED_FRONTMATTER_KEYS = {
    "id",
    "version",
    "tier",
    "output_schema",
    "max_output_tokens",
    "temperature",
    "cache_ttl_seconds",
    "description",
}


def _split_frontmatter(text: str, *, source: Path) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise PromptError(f"{source}: must start with a '---' YAML frontmatter block")
    try:
        end = lines[1:].index(FRONTMATTER_DELIMITER) + 1
    except ValueError as exc:
        raise PromptError(f"{source}: unterminated frontmatter block") from exc
    frontmatter_text = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :]).strip("\n")
    try:
        parsed = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise PromptError(f"{source}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PromptError(f"{source}: frontmatter must be a YAML mapping")
    return parsed, body


def _load_output_schema(raw: str, *, prompts_dir: Path, source: Path) -> dict[str, Any] | None:
    if raw == "text":
        return None
    schema_path = prompts_dir / raw
    if not schema_path.is_file():
        raise PromptError(f"{source}: output_schema references missing file {raw!r}")
    try:
        schema: dict[str, Any] = json.loads(schema_path.read_text())
    except json.JSONDecodeError as exc:
        raise PromptError(f"{source}: output_schema file {raw!r} is not valid JSON: {exc}") from exc
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema raises its own SchemaError subclass
        raise PromptError(
            f"{source}: output_schema file {raw!r} is not a valid JSON Schema: {exc}"
        ) from exc
    return schema


def _parse_prompt_file(path: Path, *, prompts_dir: Path) -> PromptTemplate:
    frontmatter, body = _split_frontmatter(path.read_text(), source=path)

    missing = _REQUIRED_FRONTMATTER_KEYS - frontmatter.keys()
    if missing:
        raise PromptError(f"{path}: frontmatter is missing required key(s): {sorted(missing)}")

    prompt_id = frontmatter["id"]
    if not isinstance(prompt_id, str) or not prompt_id:
        raise PromptError(f"{path}: 'id' must be a non-empty string")
    expected_filename = f"{prompt_id}.prompt.md"
    if path.name != expected_filename:
        raise PromptError(
            f"{path}: filename must match its id — expected {expected_filename!r}, "
            f"got {path.name!r}"
        )

    try:
        version = int(frontmatter["version"])
    except (TypeError, ValueError) as exc:
        raise PromptError(f"{path}: 'version' must be an integer") from exc
    if version < 1:
        raise PromptError(f"{path}: 'version' must be >= 1")

    try:
        tier = ModelTier(frontmatter["tier"])
    except ValueError as exc:
        valid = [t.value for t in ModelTier]
        raise PromptError(
            f"{path}: 'tier' must be one of {valid}, got {frontmatter['tier']!r}"
        ) from exc

    output_schema = _load_output_schema(
        str(frontmatter["output_schema"]), prompts_dir=prompts_dir, source=path
    )

    try:
        max_output_tokens = int(frontmatter["max_output_tokens"])
        if max_output_tokens < 1:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise PromptError(f"{path}: 'max_output_tokens' must be a positive integer") from exc

    try:
        temperature = float(frontmatter["temperature"])
        if not (0.0 <= temperature <= 2.0):
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise PromptError(f"{path}: 'temperature' must be a number between 0 and 2") from exc

    try:
        cache_ttl_seconds = int(frontmatter["cache_ttl_seconds"])
        if cache_ttl_seconds < 0:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise PromptError(f"{path}: 'cache_ttl_seconds' must be a non-negative integer") from exc

    description = frontmatter["description"]
    if not isinstance(description, str) or not description:
        raise PromptError(f"{path}: 'description' must be a non-empty string")

    required_context = frontmatter.get("required_context") or []
    if not isinstance(required_context, list) or not all(
        isinstance(k, str) for k in required_context
    ):
        raise PromptError(f"{path}: 'required_context' must be a list of strings")

    if not body.strip():
        raise PromptError(f"{path}: prompt body must not be empty")

    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    return PromptTemplate(
        id=prompt_id,
        version=version,
        tier=tier,
        output_schema=output_schema,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        cache_ttl_seconds=cache_ttl_seconds,
        description=description,
        required_context=list(required_context),
        body=body,
        body_hash=body_hash,
    )


def validate_required_context(template: PromptTemplate, context: Mapping[str, Any]) -> None:
    missing = [key for key in template.required_context if key not in context]
    if missing:
        raise PromptContextError(template.id, missing=missing)


class PromptRegistry:
    def __init__(self, prompts_dir: Path = DEFAULT_PROMPTS_DIR) -> None:
        self._prompts_dir = prompts_dir
        self._by_id: dict[str, PromptTemplate] = {}
        for path in sorted(prompts_dir.glob("*.prompt.md")):
            template = _parse_prompt_file(path, prompts_dir=prompts_dir)
            if template.id in self._by_id:
                raise PromptError(f"duplicate prompt id {template.id!r} in {prompts_dir}")
            self._by_id[template.id] = template
        if not self._by_id:
            raise PromptError(f"no prompt files found in {prompts_dir}")

    def get(self, prompt_id: str, *, version: int | None = None) -> PromptTemplate:
        template = self._by_id.get(prompt_id)
        if template is None:
            raise PromptNotFound(prompt_id)
        if version is not None and template.version != version:
            raise PromptVersionMismatch(prompt_id, pinned=version, current=template.version)
        return template

    def all(self) -> list[PromptTemplate]:
        return sorted(self._by_id.values(), key=lambda t: t.id)


_registry: PromptRegistry | None = None


def get_registry() -> PromptRegistry:
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def get_prompt(prompt_id: str, *, version: int | None = None) -> PromptTemplate:
    return get_registry().get(prompt_id, version=version)


def all_prompts() -> list[PromptTemplate]:
    return get_registry().all()
