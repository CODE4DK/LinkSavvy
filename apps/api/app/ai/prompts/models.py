"""The parsed, validated shape of a `.prompt.md` file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.ai.providers.base import ModelTier
from app.errors import ApiError, ErrorCode


class PromptError(Exception):
    """Raised at load time for a malformed prompt file. The registry lets
    this propagate so a bad prompt fails application startup loudly rather
    than failing the first request that happens to use it — never reaches
    a request, so it deliberately isn't an ApiError."""


class PromptNotFound(ApiError):
    def __init__(self, prompt_id: str) -> None:
        super().__init__(ErrorCode.NOT_FOUND, f"no prompt registered with id {prompt_id!r}")


class PromptVersionMismatch(ApiError):
    """Raised when a caller pins a version that isn't the one currently
    loaded for that id — protects a cached invocation or an in-flight
    integration from silently running against a since-changed template."""

    def __init__(self, prompt_id: str, *, pinned: int, current: int) -> None:
        super().__init__(
            ErrorCode.VALIDATION_FAILED,
            f"prompt {prompt_id!r} is pinned to version {pinned}, "
            f"but the currently loaded version is {current}",
        )


class PromptContextError(ApiError):
    """Raised when the context supplied to a prompt is missing a key its
    frontmatter declares as `required_context`."""

    def __init__(self, prompt_id: str, *, missing: list[str]) -> None:
        super().__init__(
            ErrorCode.VALIDATION_FAILED,
            f"prompt {prompt_id!r} is missing required context key(s): {missing}",
            details={"missing_context_keys": missing},
        )


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
