from __future__ import annotations

import pytest

from app.ai.providers.base import LLMMessage, LLMRequest, LLMRole, ModelTier
from app.ai.providers.fake_provider import FakeProvider, FixtureNotFound
from app.ai.providers.registry import (
    resolve_provider,
    resolve_secondary_provider,
    tier_timeout_seconds,
)


def _request(prompt_id: str, *, schema: dict[str, object] | None) -> LLMRequest:
    return LLMRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="hello")],
        tier=ModelTier.STANDARD,
        correlation_id="corr-1",
        prompt_id=prompt_id,
        prompt_version=1,
        response_schema=schema,
    )


def test_resolve_provider_picks_cheaper_model_for_free_plan() -> None:
    free = resolve_provider(ModelTier.STANDARD, "free")
    pro = resolve_provider(ModelTier.STANDARD, "pro")
    # Both are FakeProvider in tests (see conftest's autouse fixture), but
    # each is still bound to the model config/models.yaml assigns its plan.
    assert free.model == "gpt-4o-mini"
    assert pro.model == "gpt-4o"


def test_resolve_provider_is_deterministic_across_calls() -> None:
    first = resolve_provider(ModelTier.FAST, "free")
    second = resolve_provider(ModelTier.FAST, "free")
    assert first.model == second.model


def test_resolve_secondary_provider_is_fixed_regardless_of_tier() -> None:
    provider = resolve_secondary_provider()
    assert provider.model == "gemini-1.5-flash"


def test_tier_timeout_seconds_increases_with_tier() -> None:
    assert tier_timeout_seconds(ModelTier.FAST) < tier_timeout_seconds(ModelTier.ADVANCED)


@pytest.mark.asyncio
async def test_fake_provider_returns_parsed_object_for_schema_prompt() -> None:
    provider = FakeProvider(model="fake-model")
    response = await provider.complete(_request("profile.headline.v1", schema={"type": "object"}))
    assert response.parsed is not None
    assert "variants" in response.parsed
    assert response.finish_reason == "stop"
    assert response.provider == "fake"


@pytest.mark.asyncio
async def test_fake_provider_returns_text_for_text_prompt() -> None:
    provider = FakeProvider(model="fake-model")
    response = await provider.complete(_request("text.summarise.v1", schema=None))
    assert response.parsed is None
    assert isinstance(response.text, str) and response.text


@pytest.mark.asyncio
async def test_fake_provider_streams_then_yields_done_chunk() -> None:
    provider = FakeProvider(model="fake-model")
    chunks = [chunk async for chunk in provider.stream(_request("text.summarise.v1", schema=None))]
    assert chunks[-1].done is True
    assert chunks[-1].finish_reason == "stop"
    assembled = "".join(c.delta for c in chunks if not c.done)
    assert assembled  # the streamed text reassembles to something non-empty


@pytest.mark.asyncio
async def test_fake_provider_missing_fixture_raises_clear_error() -> None:
    provider = FakeProvider(model="fake-model")
    with pytest.raises(FixtureNotFound):
        await provider.complete(_request("no.such.prompt", schema=None))
