"""OpenAI chat-completions, spoken over plain HTTPS — no vendor SDK.

Consistent with `app/services/linkedin.py`: a thin `httpx` client against
the provider's documented REST API, so the dependency footprint stays
small and the test suite (which never imports this module for real calls,
per `tests/conftest.py`) doesn't need the SDK installed at all.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.ai.providers.base import (
    FinishReason,
    LLMChunk,
    LLMRequest,
    LLMResponse,
    ProviderError,
)
from app.settings import settings

CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

_FINISH_REASON_MAP: dict[str, FinishReason] = {
    "stop": "stop",
    "length": "length",
    "content_filter": "content_filter",
}


def _map_finish_reason(value: str | None) -> FinishReason:
    if value is None:
        return "error"
    return _FINISH_REASON_MAP.get(value, "stop")


class OpenAIProvider:
    name = "openai"

    def __init__(self, *, model: str) -> None:
        self.model = model

    def _headers(self) -> dict[str, str]:
        if not settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY is not configured", retryable=False)
        return {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

    def _body(self, request: LLMRequest, *, stream: bool) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            "stream": stream,
        }
        if request.stop:
            body["stop"] = request.stop
        if request.response_schema is not None:
            body["response_format"] = {"type": "json_object"}
        return body

    async def complete(self, request: LLMRequest) -> LLMResponse:
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    CHAT_COMPLETIONS_URL,
                    headers=self._headers(),
                    json=self._body(request, stream=False),
                )
        except httpx.TimeoutException as exc:
            raise ProviderError(f"openai request timed out: {exc}", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"openai request failed: {exc}", retryable=True) from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise ProviderError(
                f"openai returned {response.status_code}: {response.text}", retryable=True
            )
        if response.status_code != 200:
            raise ProviderError(
                f"openai returned {response.status_code}: {response.text}", retryable=False
            )

        data = response.json()
        choice = data["choices"][0]
        text = choice["message"]["content"] or ""
        parsed = None
        if request.response_schema is not None:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None  # the gateway's schema-validation step handles this
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            parsed=parsed,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            model=self.model,
            provider=self.name,
            latency_ms=(time.monotonic() - started) * 1000,
            finish_reason=_map_finish_reason(choice.get("finish_reason")),
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMChunk, None]:
        tokens_out_estimate = 0
        finish_reason: FinishReason = "stop"
        try:
            async with (
                httpx.AsyncClient(timeout=60) as client,
                client.stream(
                    "POST",
                    CHAT_COMPLETIONS_URL,
                    headers=self._headers(),
                    json=self._body(request, stream=True),
                ) as response,
            ):
                if response.status_code == 429 or response.status_code >= 500:
                    body = await response.aread()
                    raise ProviderError(
                        f"openai returned {response.status_code}: {body!r}", retryable=True
                    )
                if response.status_code != 200:
                    body = await response.aread()
                    raise ProviderError(
                        f"openai returned {response.status_code}: {body!r}", retryable=False
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[len("data: ") :]
                    if payload == "[DONE]":
                        break
                    event = json.loads(payload)
                    choice = event["choices"][0]
                    delta = choice.get("delta", {}).get("content") or ""
                    if delta:
                        tokens_out_estimate += max(1, len(delta) // 4)
                        yield LLMChunk(delta=delta)
                    if choice.get("finish_reason"):
                        finish_reason = _map_finish_reason(choice["finish_reason"])
        except httpx.TimeoutException as exc:
            raise ProviderError(f"openai stream timed out: {exc}", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"openai stream failed: {exc}", retryable=True) from exc

        tokens_in = sum(len(m.content) for m in request.messages) // 4 or 1
        yield LLMChunk(
            delta="",
            done=True,
            finish_reason=finish_reason,
            tokens_in=tokens_in,
            tokens_out=tokens_out_estimate,
            model=self.model,
            provider=self.name,
        )
