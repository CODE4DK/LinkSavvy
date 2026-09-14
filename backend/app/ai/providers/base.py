"""The one interface every LLM vendor integration must satisfy.

Nothing outside `app/ai/providers/` and `config/models.yaml` may reference a
vendor model string — every other module (prompts, the gateway, hub
features in later phases) speaks only in `ModelTier`. That's the point of
this abstraction: swapping a vendor, or adding a new one, never touches a
prompt template or a caller.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal, Protocol


class ModelTier(StrEnum):
    """A prompt's declared capability need, not a vendor model name.

    `config/models.yaml` maps `(tier, plan)` to the concrete model that
    actually serves a request.
    """

    FAST = "fast"
    STANDARD = "standard"
    ADVANCED = "advanced"


class LLMRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: LLMRole
    content: str


@dataclass(frozen=True, slots=True)
class LLMRequest:
    messages: list[LLMMessage]
    tier: ModelTier
    correlation_id: str
    # The gateway always knows which prompt it's running (it's `run()`'s
    # own argument) — these travel with the request anyway so a provider
    # can tag outbound telemetry with them, and so `FakeProvider` can pick
    # the right fixture without parsing rendered prompt text.
    prompt_id: str
    prompt_version: int
    response_schema: dict[str, Any] | None = None
    max_output_tokens: int = 1024
    temperature: float = 0.7
    stop: list[str] = field(default_factory=list)


FinishReason = Literal["stop", "length", "content_filter", "error"]


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str | None
    parsed: Any | None
    tokens_in: int
    tokens_out: int
    model: str
    provider: str
    latency_ms: float
    finish_reason: FinishReason


@dataclass(frozen=True, slots=True)
class LLMChunk:
    """One frame of a streamed completion.

    `delta` carries incremental text. The final chunk of a stream has
    `done=True` and carries the same accounting fields as `LLMResponse`
    (`finish_reason`, `tokens_in`, `tokens_out`) so callers don't need a
    separate trailing message to learn how the stream ended.
    """

    delta: str
    done: bool = False
    finish_reason: FinishReason | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    model: str | None = None
    provider: str | None = None


class ProviderError(Exception):
    """Raised by a provider on any failure the gateway should retry or
    fall back on: HTTP 429/5xx, timeouts, and malformed responses."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMProvider(Protocol):
    """Implemented by `openai_provider`, `gemini_provider`, and
    `fake_provider`. Each instance is bound to one concrete model (see
    `app.ai.providers.registry.resolve_provider`, which is the only place
    `config/models.yaml` is read) — `request.tier` travels along for
    logging only, never for model selection inside the provider. The
    gateway never imports a concrete provider class directly."""

    name: str
    model: str

    async def complete(self, request: LLMRequest) -> LLMResponse: ...

    def stream(self, request: LLMRequest) -> AsyncGenerator[LLMChunk, None]: ...
