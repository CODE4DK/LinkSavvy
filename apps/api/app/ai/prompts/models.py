"""The parsed, validated shape of a `.prompt.md` file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.ai.providers.base import ModelTier


class PromptError(Exception):
    """Raised at load time for a malformed prompt file. The registry lets
    this propagate so a bad prompt fails application startup loudly rather
    than failing the first request that happens to use it."""


class PromptNotFound(Exception):
    pass


class PromptVersionMismatch(Exception):
    """Raised when a caller pins a version that isn't the one currently
    loaded for that id — protects a cached invocation or an in-flight
    integration from silently running against a since-changed template."""


class PromptContextError(Exception):
    """Raised when the context supplied to a prompt is missing a key its
    frontmatter declares as `required_context`."""


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    id: str
    version: int
    tier: ModelTier
    output_schema: dict[str, Any] | None  # None means the prompt returns plain text
    max_output_tokens: int
    temperature: float
    cache_ttl_seconds: int
    description: str
    required_context: list[str] = field(default_factory=list)
    body: str = ""
    body_hash: str = ""
