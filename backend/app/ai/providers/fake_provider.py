"""A deterministic, fixture-driven stand-in for a real vendor.

Every test in this codebase goes through `FakeProvider`, never a real
vendor SDK or HTTP call — see `tests/conftest.py`'s autouse
`_fake_ai_providers` fixture, which swaps both `openai` and `gemini`
provider classes for this one for the whole test session. Responses come
from JSON fixture files keyed by prompt id, so the same prompt always
produces the same canned output: golden tests can assert on it exactly.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from app.ai.providers.base import LLMChunk, LLMRequest, LLMResponse

DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent / "fake_fixtures"


class FixtureNotFound(Exception):
    pass


class FakeProvider:
    name = "fake"

    def __init__(self, *, model: str = "fake-model", fixtures_dir: Path = DEFAULT_FIXTURES_DIR):
        self.model = model
        self.fixtures_dir = fixtures_dir

    def _load_fixture(self, prompt_id: str) -> dict[str, Any]:
        path = self.fixtures_dir / f"{prompt_id}.json"
        if not path.exists():
            raise FixtureNotFound(
                f"no fake-provider fixture for prompt {prompt_id!r} at {path} — "
                "add one under app/ai/providers/fake_fixtures/"
            )
        result: dict[str, Any] = json.loads(path.read_text())
        return result

    def _render(self, request: LLMRequest) -> tuple[str, Any, int]:
        fixture = self._load_fixture(request.prompt_id)
        if request.response_schema is not None:
            parsed = fixture["response"]
            text = json.dumps(parsed)
        else:
            parsed = None
            text = (
                fixture["response"]["text"]
                if isinstance(fixture["response"], dict)
                else fixture["response"]
            )
        tokens_out = fixture.get("tokens_out", max(1, len(text) // 4))
        return text, parsed, tokens_out

    async def complete(self, request: LLMRequest) -> LLMResponse:
        started = time.monotonic()
        text, parsed, tokens_out = self._render(request)
        tokens_in = sum(len(m.content) for m in request.messages) // 4 or 1
        return LLMResponse(
            text=text,
            parsed=parsed,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=self.model,
            provider=self.name,
            latency_ms=(time.monotonic() - started) * 1000,
            finish_reason="stop",
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMChunk, None]:
        text, _parsed, tokens_out = self._render(request)
        tokens_in = sum(len(m.content) for m in request.messages) // 4 or 1
        chunk_size = max(1, len(text) // 5)
        for start in range(0, len(text), chunk_size):
            yield LLMChunk(delta=text[start : start + chunk_size])
        yield LLMChunk(
            delta="",
            done=True,
            finish_reason="stop",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=self.model,
            provider=self.name,
        )
