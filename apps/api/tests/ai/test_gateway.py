from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.ai.gateway import AIOutputInvalid, AIProviderUnavailable
from app.ai.prompts.models import PromptContextError, PromptTemplate
from app.ai.providers import registry
from app.ai.providers.base import (
    LLMChunk,
    LLMRequest,
    LLMResponse,
    ModelTier,
    ProviderError,
)
from app.ai.safety.output_policy import OutputPolicyViolation
from app.billing.quota import QuotaExceeded
from app.models.ai_invocation import AIInvocation
from app.models.usage_counter import UsageCounter
from app.models.user import User


def _template(
    *,
    prompt_id: str,
    body: str,
    output_schema: dict[str, object] | None,
    required_context: list[str] | None = None,
    tier: ModelTier = ModelTier.STANDARD,
    cache_ttl_seconds: int = 0,
) -> PromptTemplate:
    return PromptTemplate(
        id=prompt_id,
        version=1,
        tier=tier,
        output_schema=output_schema,
        max_output_tokens=200,
        temperature=0.7,
        cache_ttl_seconds=cache_ttl_seconds,
        description="test prompt",
        required_context=required_context or [],
        body=body,
        body_hash="deadbeef",
    )


HEADLINE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"variants": {"type": "array"}},
    "required": ["variants"],
}


class _StubProvider:
    """A minimal LLMProvider double for exercising retry/fallback/repair
    paths the fixture-driven FakeProvider can't (since its fixtures are
    shared, deterministic golden data)."""

    def __init__(self, name: str, model: str, *, responses: list[object]) -> None:
        self.name = name
        self.model = model
        self._responses = list(responses)
        self.calls = 0

    async def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        outcome = self._responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, LLMResponse)
        return outcome

    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMChunk, None]:
        self.calls += 1
        outcome = self._responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, list)
        for chunk in outcome:
            yield chunk


def _ok_response(
    *, text: str, parsed: object = None, model: str = "gpt-4o-mini", provider: str = "stub"
) -> LLMResponse:
    return LLMResponse(
        text=text,
        parsed=parsed,
        tokens_in=10,
        tokens_out=5,
        model=model,
        provider=provider,
        latency_ms=1.0,
        finish_reason="stop",
    )


async def _create_user(db: AsyncSession, *, plan: str = "free") -> User:
    user = User(email=f"gw-{uuid.uuid4()}@example.com", full_name="Gateway Tester", plan=plan)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_happy_path_with_schema_records_ok_invocation(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="profile.headline.v1",
        body="Write headlines for: {{ profile_text }}",
        output_schema=HEADLINE_SCHEMA,
        required_context=["profile_text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    result = await gateway.run(
        "profile.headline.v1", {"profile_text": "Backend engineer"}, user=user, db=db_session
    )

    assert result.cached is False
    assert result.parsed is not None
    assert "variants" in result.parsed
    assert result.cost_minor >= 0

    invocation = (
        await db_session.execute(
            select(AIInvocation).where(AIInvocation.correlation_id == result.correlation_id)
        )
    ).scalar_one()
    assert invocation.outcome == "ok"
    assert invocation.cached is False


async def test_happy_path_text_only_prompt(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    result = await gateway.run(
        "text.summarise.v1", {"text": "some long text"}, user=user, db=db_session
    )
    assert result.parsed is None
    assert isinstance(result.text, str) and result.text


async def test_missing_required_context_raises_before_any_quota_use(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    with pytest.raises(PromptContextError):
        await gateway.run("text.summarise.v1", {}, user=user, db=db_session)

    counters = (await db_session.execute(select(UsageCounter))).scalars().all()
    assert len(counters) == 0


async def test_second_identical_call_is_served_from_cache(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
        cache_ttl_seconds=3600,
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    first = await gateway.run("text.summarise.v1", {"text": "same input"}, user=user, db=db_session)
    second = await gateway.run(
        "text.summarise.v1", {"text": "same input"}, user=user, db=db_session
    )

    assert first.cached is False
    assert second.cached is True
    assert second.text == first.text

    counter = (
        await db_session.execute(select(UsageCounter).where(UsageCounter.user_id == user.id))
    ).scalar_one()
    assert counter.used == 1  # the cache hit never reserved quota


async def test_quota_denied_is_recorded_and_raised(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    for i in range(20):  # free/ai_runs seeded limit
        await gateway.run("text.summarise.v1", {"text": f"input {i}"}, user=user, db=db_session)

    with pytest.raises(QuotaExceeded):
        await gateway.run("text.summarise.v1", {"text": "one too many"}, user=user, db=db_session)

    denied = (
        (
            await db_session.execute(
                select(AIInvocation).where(AIInvocation.outcome == "quota_denied")
            )
        )
        .scalars()
        .all()
    )
    assert len(denied) == 1


async def test_retry_exhaustion_falls_back_to_secondary_provider(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)
    monkeypatch.setattr(gateway, "BASE_BACKOFF_SECONDS", 0.001)

    primary = _StubProvider(
        "primary",
        "gpt-4o-mini",
        responses=[ProviderError("boom", retryable=True) for _ in range(gateway.MAX_RETRIES)],
    )
    secondary = _StubProvider(
        "gemini",
        "gemini-1.5-flash",
        responses=[_ok_response(text="fallback text", model="gemini-1.5-flash", provider="gemini")],
    )
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary)
    monkeypatch.setattr(registry, "resolve_secondary_provider", lambda: secondary)

    result = await gateway.run("text.summarise.v1", {"text": "hi"}, user=user, db=db_session)

    assert result.fallback_used is True
    assert result.provider == "gemini"
    assert primary.calls == gateway.MAX_RETRIES
    assert secondary.calls == 1


async def test_both_providers_failing_raises_and_releases_quota(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)
    monkeypatch.setattr(gateway, "BASE_BACKOFF_SECONDS", 0.001)

    primary = _StubProvider(
        "primary",
        "gpt-4o-mini",
        responses=[ProviderError("boom", retryable=True) for _ in range(gateway.MAX_RETRIES)],
    )
    secondary = _StubProvider(
        "gemini",
        "gemini-1.5-flash",
        responses=[ProviderError("also boom", retryable=True) for _ in range(gateway.MAX_RETRIES)],
    )
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary)
    monkeypatch.setattr(registry, "resolve_secondary_provider", lambda: secondary)

    with pytest.raises(AIProviderUnavailable):
        await gateway.run("text.summarise.v1", {"text": "hi"}, user=user, db=db_session)

    counter = (
        await db_session.execute(select(UsageCounter).where(UsageCounter.user_id == user.id))
    ).scalar_one()
    assert counter.used == 0  # reservation was released

    invocation = (
        await db_session.execute(
            select(AIInvocation).where(AIInvocation.outcome == "provider_error")
        )
    ).scalar_one()
    assert invocation.outcome == "provider_error"


async def test_non_retryable_provider_error_skips_straight_to_fallback(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    primary = _StubProvider(
        "primary", "gpt-4o-mini", responses=[ProviderError("misconfigured", retryable=False)]
    )
    secondary = _StubProvider(
        "gemini", "gemini-1.5-flash", responses=[_ok_response(text="fallback")]
    )
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary)
    monkeypatch.setattr(registry, "resolve_secondary_provider", lambda: secondary)

    result = await gateway.run("text.summarise.v1", {"text": "hi"}, user=user, db=db_session)
    assert result.fallback_used is True
    assert primary.calls == 1  # no retries for a non-retryable error


async def test_schema_repair_succeeds_on_second_attempt(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="profile.headline.v1",
        body="Write headlines for: {{ profile_text }}",
        output_schema=HEADLINE_SCHEMA,
        required_context=["profile_text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    primary = _StubProvider(
        "primary",
        "gpt-4o-mini",
        responses=[
            _ok_response(text="not json at all"),
            _ok_response(text='{"variants": [{"text": "a", "rationale": "b", "keywords": []}]}'),
        ],
    )
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary)

    result = await gateway.run(
        "profile.headline.v1", {"profile_text": "hi"}, user=user, db=db_session
    )
    assert result.parsed is not None
    assert primary.calls == 2


async def test_schema_repair_failure_raises_invalid_output_and_releases_quota(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="profile.headline.v1",
        body="Write headlines for: {{ profile_text }}",
        output_schema=HEADLINE_SCHEMA,
        required_context=["profile_text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    primary = _StubProvider(
        "primary",
        "gpt-4o-mini",
        responses=[_ok_response(text="not json"), _ok_response(text="still not json")],
    )
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary)

    with pytest.raises(AIOutputInvalid):
        await gateway.run("profile.headline.v1", {"profile_text": "hi"}, user=user, db=db_session)

    counter = (
        await db_session.execute(select(UsageCounter).where(UsageCounter.user_id == user.id))
    ).scalar_one()
    assert counter.used == 0
    invocation = (
        await db_session.execute(
            select(AIInvocation).where(AIInvocation.outcome == "invalid_output")
        )
    ).scalar_one()
    assert invocation.outcome == "invalid_output"


async def test_output_policy_violation_blocks_and_releases_quota(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    primary = _StubProvider(
        "primary",
        "gpt-4o-mini",
        responses=[_ok_response(text="You should use a bot to auto-connect with people.")],
    )
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary)

    with pytest.raises(OutputPolicyViolation):
        await gateway.run("text.summarise.v1", {"text": "hi"}, user=user, db=db_session)

    counter = (
        await db_session.execute(select(UsageCounter).where(UsageCounter.user_id == user.id))
    ).scalar_one()
    assert counter.used == 0
    invocation = (
        await db_session.execute(
            select(AIInvocation).where(AIInvocation.outcome == "policy_blocked")
        )
    ).scalar_one()
    assert invocation.outcome == "policy_blocked"


async def test_stream_yields_meta_delta_and_done_frames(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    primary = _StubProvider(
        "primary",
        "gpt-4o-mini",
        responses=[
            [
                LLMChunk(delta="Hello "),
                LLMChunk(delta="world"),
                LLMChunk(
                    delta="",
                    done=True,
                    finish_reason="stop",
                    tokens_in=5,
                    tokens_out=3,
                    model="gpt-4o-mini",
                    provider="primary",
                ),
            ]
        ],
    )
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary)

    frames = [
        frame
        async for frame in gateway.run(
            "text.summarise.v1", {"text": "hi"}, user=user, db=db_session, stream=True
        )
    ]

    types = [f["type"] for f in frames]
    assert types == ["meta", "delta", "delta", "done"]
    assert "".join(f["text"] for f in frames if f["type"] == "delta") == "Hello world"

    invocation = (
        await db_session.execute(select(AIInvocation).where(AIInvocation.outcome == "ok"))
    ).scalar_one()
    assert invocation.tokens_out == 3


async def test_stream_cache_hit_skips_the_provider(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
        cache_ttl_seconds=3600,
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    await gateway.run("text.summarise.v1", {"text": "same"}, user=user, db=db_session)

    primary_after_cache = _StubProvider("primary", "gpt-4o-mini", responses=[])
    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: primary_after_cache)

    frames = [
        frame
        async for frame in gateway.run(
            "text.summarise.v1", {"text": "same"}, user=user, db=db_session, stream=True
        )
    ]
    assert frames[0]["cached"] is True
    assert primary_after_cache.calls == 0


async def test_stream_client_cancellation_closes_the_upstream_generator(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    template = _template(
        prompt_id="text.summarise.v1",
        body="Summarize: {{ text }}",
        output_schema=None,
        required_context=["text"],
    )
    monkeypatch.setattr(gateway, "get_prompt", lambda prompt_id: template)

    closed = False

    class _CancelableProvider:
        name = "primary"
        model = "gpt-4o-mini"

        async def complete(self, request: LLMRequest) -> LLMResponse:  # pragma: no cover
            raise NotImplementedError

        async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMChunk, None]:
            nonlocal closed
            try:
                yield LLMChunk(delta="partial")
                yield LLMChunk(delta="more")
            finally:
                closed = True

    monkeypatch.setattr(registry, "resolve_provider", lambda tier, plan: _CancelableProvider())

    agen = gateway.run("text.summarise.v1", {"text": "hi"}, user=user, db=db_session, stream=True)
    first = await agen.__anext__()
    assert first["type"] == "meta"
    second = await agen.__anext__()
    assert second["type"] == "delta"
    await agen.aclose()

    assert closed is True
