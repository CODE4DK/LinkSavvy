"""Auto-discovers every `ToolDefinition` under `app/tools/definitions/`,
validates each one's `prompt_id` resolves to a real prompt whose
declared output schema matches the definition's own `output_schema`
Pydantic model, and exposes lookup/listing.

Loaded eagerly by `app/main.py` (mirroring `app/ai/prompts/loader.py`'s
`get_registry()`) so a broken tool definition fails application
startup, never a request.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from app.ai.prompts.loader import get_prompt
from app.ai.prompts.models import PromptNotFound
from app.tools.definition import Hub, ToolDefinition
from app.tools.errors import ToolDefinitionError, ToolNotFound

DEFAULT_DEFINITIONS_DIR = Path(__file__).resolve().parent / "definitions"


def _module_name_for(path: Path, *, definitions_dir: Path) -> str:
    relative = path.relative_to(definitions_dir).with_suffix("")
    return ".".join(["app", "tools", "definitions", *relative.parts])


def _load_definition_module(path: Path, *, definitions_dir: Path) -> ToolDefinition:
    module_name = _module_name_for(path, definitions_dir=definitions_dir)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ToolDefinitionError(f"{path}: could not load module spec")
    module = importlib.util.module_from_spec(spec)
    # Registered before exec so a definition file can declare nested
    # output models (`list[SomeSubModel]`) -- under `from __future__
    # import annotations`, Pydantic resolves those forward references by
    # looking the module up in `sys.modules` by name, which fails silently
    # (well, loudly: "X is not fully defined") for a module that only
    # exists as a bare object never registered there.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    definition = getattr(module, "DEFINITION", None)
    if not isinstance(definition, ToolDefinition):
        raise ToolDefinitionError(
            f"{path}: must define a module-level `DEFINITION: ToolDefinition`"
        )
    return definition


def _validate_against_prompt(definition: ToolDefinition, *, source: Path) -> None:
    try:
        template = get_prompt(definition.prompt_id)
    except PromptNotFound as exc:
        raise ToolDefinitionError(
            f"{source}: tool {definition.id!r} references unknown prompt "
            f"{definition.prompt_id!r}"
        ) from exc

    if template.output_schema is None:
        raise ToolDefinitionError(
            f"{source}: tool {definition.id!r}'s prompt {definition.prompt_id!r} declares "
            "output_schema: text -- every tool needs a structured JSON output"
        )

    expected = definition.output_schema.model_json_schema()
    if template.output_schema != expected:
        raise ToolDefinitionError(
            f"{source}: tool {definition.id!r}'s output_schema Pydantic model doesn't match "
            f"its prompt {definition.prompt_id!r}'s declared schema file -- regenerate the "
            "prompt's schema JSON from `output_schema.model_json_schema()`"
        )


class ToolRegistry:
    def __init__(self, definitions_dir: Path = DEFAULT_DEFINITIONS_DIR) -> None:
        self._by_id: dict[str, ToolDefinition] = {}
        for path in sorted(definitions_dir.rglob("*.py")):
            if path.name in ("__init__.py",):
                continue
            definition = _load_definition_module(path, definitions_dir=definitions_dir)
            if definition.id in self._by_id:
                raise ToolDefinitionError(f"{path}: duplicate tool id {definition.id!r}")
            _validate_against_prompt(definition, source=path)
            self._by_id[definition.id] = definition
        # Unlike prompts (core infra that always ships with seed prompts),
        # an empty tool catalog is a valid state -- a hub can land before
        # any of its tools do.

    def get(self, tool_id: str) -> ToolDefinition:
        try:
            return self._by_id[tool_id]
        except KeyError as exc:
            raise ToolNotFound(tool_id) from exc

    def all(self) -> list[ToolDefinition]:
        return sorted(self._by_id.values(), key=lambda definition: definition.id)

    def by_hub(self, hub: Hub) -> list[ToolDefinition]:
        return [definition for definition in self.all() if definition.hub == hub]


_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def get_tool(tool_id: str) -> ToolDefinition:
    return get_registry().get(tool_id)


def all_tools() -> list[ToolDefinition]:
    return get_registry().all()


def outreach_tool_ids() -> list[str]:
    """Every tool id flagged `counts_as_outreach=True` -- the daily soft
    cap (app/engagement/guardrails.py) is on outreach volume across all
    of them, not on any one tool. Routed through this module's own
    `get_registry()` (rather than called directly from app/tools/
    service.py) so tests can swap the registry the same way they
    already do for `get_tool`."""
    return [definition.id for definition in get_registry().all() if definition.counts_as_outreach]
