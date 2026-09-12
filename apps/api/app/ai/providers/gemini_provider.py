"""Google Gemini `generateContent`, spoken over plain HTTPS — no vendor SDK.

Same rationale as `openai_provider.py`: a thin `httpx` client, no SDK
dependency, never called by the test suite (see `tests/conftest.py`).
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.ai.providers.base import (
    FinishReason,
    LLMChunk,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    LLMRole,
    ProviderError,
)
from app.settings import settings

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

_FINISH_REASON_MAP: dict[str, FinishReason] = {
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "content_filter",
    "RECITATION": "content_filter",
}


def _map_finish_reason(value: str | None) -> FinishReason:
    if value is None:
        return "error"
    return _FINISH_REASON_MAP.get(value, "stop")


def _split_system_instruction(messages: list[LLMMessage]) -> tuple[str | None, list[LLMMessage]]:
    system_parts = [m.content for m in messages if m.role == LLMRole.SYSTEM]
    rest = [m for m in messages if m.role != LLMRole.SYSTEM]
    return ("\n\n".join(system_parts) or None, rest)


def _to_contents(messages: list[LLMMessage]) -> list[dict[str, Any]]:
    role_map = {LLMRole.USER: "user", LLMRole.ASSISTANT: "model"}
    return [{"role": role_map[m.role], "parts": [{"text": m.content}]} for m in messages]


class GeminiProvider:
    name = "gemini"

    def __init__(self, *, model: str) -> None:
        self.model = model

    def _url(self, *, stream: bool) -> str:
        if not settings.gemini_api_key:
            raise ProviderError("GEMINI_API_KEY is not configured", retryable=False)
        method = "streamGenerateContent" if stream else "generateContent"
        return f"{BASE_URL}/{self.model}:{method}?key={settings.gemini_api_key}"

    def _body(self, request: LLMRequest) -> dict[str, Any]:
        system_instruction, rest = _split_system_instruction(request.messages)
        generation_config: dict[str, Any] = {
            "maxOutputTokens": request.max_output_tokens,
            "temperature": request.temperature,
        }
        if request.stop:
            generation_config["stopSequences"] = request.stop
        if request.response_schema is not None:
            generation_config["responseMimeType"] = "application/json"
        body: dict[str, Any] = {
            "contents": _to_contents(rest),
            "generationConfig": generation_config,
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        return body

    async def complete(self, request: LLMRequest) -> LLMResponse:
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self._url(stream=False),
                    json=self._body(request),
                )
        except httpx.TimeoutException as exc:
            raise ProviderError(f"gemini request timed out: {exc}", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"gemini request failed: {exc}", retryable=True) from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise ProviderError(
                f"gemini returned {response.status_code}: {response.text}", retryable=True
            )
        if response.status_code != 200:
            raise ProviderError(
                f"gemini returned {response.status_code}: {response.text}", retryable=False
            )

        data = response.json()
        candidate = data["candidates"][0]
        text = "".join(part.get("text", "") for part in candidate["content"]["parts"])
        parsed = None
        if request.response_schema is not None:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
        usage = data.get("usageMetadata", {})
        return LLMResponse(
            text=text,
            parsed=parsed,
            tokens_in=usage.get("promptTokenCount", 0),
            tokens_out=usage.get("candidatesTokenCount", 0),
            model=self.model,
            provider=self.name,
            latency_ms=(time.monotonic() - started) * 1000,
            finish_reason=_map_finish_reason(candidate.get("finishReason")),
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        tokens_out_estimate = 0
        finish_reason: FinishReason = "stop"
        try:
            async with (
                httpx.AsyncClient(timeout=60) as client,
                client.stream(
                    "POST",
                    self._url(stream=True) + "&alt=sse",
                    json=self._body(request),
                ) as response,
            ):
                if response.status_code == 429 or response.status_code >= 500:
                    body = await response.aread()
                    raise ProviderError(
                        f"gemini returned {response.status_code}: {body!r}", retryable=True
                    )
                if response.status_code != 200:
                    body = await response.aread()
                    raise ProviderError(
                        f"gemini returned {response.status_code}: {body!r}", retryable=False
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    event = json.loads(line[len("data: ") :])
                    candidate = event["candidates"][0]
                    delta = "".join(part.get("text", "") for part in candidate["content"]["parts"])
                    if delta:
                        tokens_out_estimate += max(1, len(delta) // 4)
                        yield LLMChunk(delta=delta)
                    if candidate.get("finishReason"):
                        finish_reason = _map_finish_reason(candidate["finishReason"])
        except httpx.TimeoutException as exc:
            raise ProviderError(f"gemini stream timed out: {exc}", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"gemini stream failed: {exc}", retryable=True) from exc

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
