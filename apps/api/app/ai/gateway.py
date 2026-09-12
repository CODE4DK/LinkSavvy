"""The one entrypoint every AI-backed feature calls: `run()`.

Everything downstream of a prompt template — provider selection, caching,
quota, retries, fallback, schema repair, and the safety checks on both
sides — happens here, exactly once, so a later phase adding a hub feature
writes a prompt template and calls `run(prompt_id, context, user=..., db=...)`
instead of touching a vendor SDK, a cache, or a quota table itself.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
import uuid
from collections.abc import AsyncIterator, Mapping
from contextlib import aclosing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from jsonschema.validators import Draft202012Validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.circuit_breaker import circuit_breaker
from app.ai.prompts.loader import get_prompt, validate_required_context
from app.ai.prompts.models import PromptTemplate
from app.ai.prompts.render import render_prompt
from app.ai.providers import registry
from app.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMRole,
    ModelTier,
    ProviderError,
)
from app.ai.safety.output_policy import OutputPolicyViolation, check_output_policy
from app.ai.safety.sanitize import sanitize_context
from app.billing.quota import check_and_reserve, release
from app.errors import ApiError, ErrorCode
from app.models.ai_cache import AICache
from app.models.ai_invocation import AIInvocation
from app.models.user import User

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 0.5

Outcome = Literal["ok", "invalid_output", "provider_error", "quota_denied", "policy_blocked"]


class AIOutputInvalid(ApiError):
    def __init__(self, prompt_id: str) -> None:
        super().__init__(
            ErrorCode.AI_OUTPUT_INVALID,
            f"the model's output for {prompt_id!r} did not satisfy the required schema, "
            "even after one repair attempt",
        )


class AIProviderUnavailable(ApiError):
    def __init__(self, prompt_id: str) -> None:
        super().__init__(
            ErrorCode.AI_PROVIDER_UNAVAILABLE,
            f"no provider could serve {prompt_id!r} right now — please try again shortly",
        )


@dataclass(frozen=True, slots=True)
class GatewayResult:
    text: str | None
    parsed: Any | None
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    cost_minor: int
    currency: str
    latency_ms: float
    cached: bool
    fallback_used: bool
    correlation_id: str
    invocation_id: uuid.UUID


def _canonical_json(context: Mapping[str, Any]) -> str:
    return json.dumps(context, sort_keys=True, separators=(",", ":"), default=str)


def compute_cache_key(
    *, prompt_id: str, version: int, context: Mapping[str, Any], tier: ModelTier, model: str
) -> str:
    raw = f"{prompt_id}:{version}:{_canonical_json(context)}:{tier.value}:{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _estimate_cost_minor(*, model: str, tokens_in: int, tokens_out: int) -> int:
    input_rate, output_rate = registry.cost_per_million_tokens_minor(model)
    cost = (tokens_in * input_rate + tokens_out * output_rate) / 1_000_000
    return round(cost)


async def _get_cache_entry(db: AsyncSession, cache_key: str) -> AICache | None:
    now = datetime.now(UTC)
    return (
        await db.execute(
            select(AICache).where(AICache.cache_key == cache_key, AICache.expires_at > now)
        )
    ).scalar_one_or_none()


async def _store_cache_entry(
    db: AsyncSession,
    *,
    cache_key: str,
    prompt_id: str,
    prompt_version: int,
    text: str | None,
    parsed: Any,
    tokens: int,
    ttl_seconds: int,
) -> None:
    if ttl_seconds <= 0:
        return
    entry = AICache(
        cache_key=cache_key,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        response={"text": text, "parsed": parsed},
        tokens=tokens,
        expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
    )
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError:
        # Another request cached the same key first (same prompt, context,
        # tier and model) — the cache is fine either way, no-op.
        await db.rollback()


async def _record_invocation(
    db: AsyncSession,
    *,
    user: User,
    template: PromptTemplate,
    tier: ModelTier,
    provider_name: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    cost_minor: int,
    latency_ms: float,
    cached: bool,
    fallback_used: bool,
    outcome: Outcome,
    correlation_id: str,
) -> AIInvocation:
    invocation = AIInvocation(
        user_id=user.id,
        prompt_id=template.id,
        prompt_version=template.version,
        tier=tier.value,
        provider=provider_name,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_minor=cost_minor,
        currency=registry.currency(),
        latency_ms=round(latency_ms),
        cached=cached,
        fallback_used=fallback_used,
        outcome=outcome,
        correlation_id=correlation_id,
    )
    db.add(invocation)
    await db.commit()
    await db.refresh(invocation)
    return invocation


async def _call_with_retry(
    provider: LLMProvider, request: LLMRequest, *, timeout: float
) -> LLMResponse:
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return await asyncio.wait_for(provider.complete(request), timeout=timeout)
        except ProviderError as exc:
            last_exc = exc
            if not exc.retryable:
                raise
        except TimeoutError as exc:
            last_exc = exc
        if attempt < MAX_RETRIES - 1:
            backoff = BASE_BACKOFF_SECONDS * (2**attempt) + random.uniform(0, BASE_BACKOFF_SECONDS)
            await asyncio.sleep(backoff)
    assert last_exc is not None
    raise last_exc


async def _call_with_fallback(
    provider: LLMProvider, request: LLMRequest, *, tier: ModelTier
) -> tuple[LLMResponse, bool]:
    """Tries the primary provider (unless its circuit breaker is open),
    retrying transient failures, then falls back to the secondary provider
    on exhaustion. Raises AIProviderUnavailable only if both fail."""
    timeout = registry.tier_timeout_seconds(tier)
    if not circuit_breaker.is_open(provider.name):
        try:
            response = await _call_with_retry(provider, request, timeout=timeout)
            circuit_breaker.record_success(provider.name)
            return response, False
        except (ProviderError, TimeoutError):
            circuit_breaker.record_failure(provider.name)

    secondary = registry.resolve_secondary_provider()
    secondary_timeout = registry.tier_timeout_seconds(ModelTier.STANDARD)
    try:
        response = await _call_with_retry(secondary, request, timeout=secondary_timeout)
        circuit_breaker.record_success(secondary.name)
        return response, True
    except (ProviderError, TimeoutError) as exc:
        circuit_breaker.record_failure(secondary.name)
        raise AIProviderUnavailable(request.prompt_id) from exc


def _validate_against_schema(
    *, text: str | None, parsed: Any, schema: dict[str, Any]
) -> tuple[bool, Any]:
    if parsed is None:
        try:
            parsed = json.loads(text or "")
        except json.JSONDecodeError:
            return False, None
    try:
        Draft202012Validator(schema).validate(parsed)
    except JsonSchemaValidationError:
        return False, None
    return True, parsed


def _build_messages(rendered_prompt: str) -> list[LLMMessage]:
    return [LLMMessage(role=LLMRole.USER, content=rendered_prompt)]


def _repair_request(original: LLMRequest, invalid_text: str, schema: dict[str, Any]) -> LLMRequest:
    repair_instruction = (
        "Your previous output did not satisfy this schema; return only valid JSON.\n"
        f"Schema: {json.dumps(schema)}"
    )
    messages = [
        *original.messages,
        LLMMessage(role=LLMRole.ASSISTANT, content=invalid_text),
        LLMMessage(role=LLMRole.USER, content=repair_instruction),
    ]
    return LLMRequest(
        messages=messages,
        tier=original.tier,
        correlation_id=original.correlation_id,
        prompt_id=original.prompt_id,
        prompt_version=original.prompt_version,
        response_schema=original.response_schema,
        max_output_tokens=original.max_output_tokens,
        temperature=original.temperature,
        stop=original.stop,
    )


async def _complete(
    prompt_id: str,
    context: Mapping[str, Any],
    *,
    user: User,
    db: AsyncSession,
    tier_override: ModelTier | None,
    idempotency_key: str | None,
) -> GatewayResult:
    correlation_id = idempotency_key or str(uuid.uuid4())
    template = get_prompt(prompt_id)
    tier = tier_override or template.tier

    # 1. Validate context
    validate_required_context(template, context)

    # 2. Sanitize
    sanitized_context = sanitize_context(context)

    provider = registry.resolve_provider(tier, user.plan)

    # 3. Cache check
    cache_key = compute_cache_key(
        prompt_id=template.id,
        version=template.version,
        context=context,
        tier=tier,
        model=provider.model,
    )
    cached_entry = await _get_cache_entry(db, cache_key)
    if cached_entry is not None:
        invocation = await _record_invocation(
            db,
            user=user,
            template=template,
            tier=tier,
            provider_name=provider.name,
            model=provider.model,
            tokens_in=0,
            tokens_out=cached_entry.tokens,
            cost_minor=0,
            latency_ms=0.0,
            cached=True,
            fallback_used=False,
            outcome="ok",
            correlation_id=correlation_id,
        )
        payload = cached_entry.response
        return GatewayResult(
            text=payload.get("text"),
            parsed=payload.get("parsed"),
            model=provider.model,
            provider=provider.name,
            tokens_in=0,
            tokens_out=cached_entry.tokens,
            cost_minor=0,
            currency=registry.currency(),
            latency_ms=0.0,
            cached=True,
            fallback_used=False,
            correlation_id=correlation_id,
            invocation_id=invocation.id,
        )

    # 4. Quota
    try:
        reservation = await check_and_reserve(db, user=user, metric="ai_runs")
    except ApiError:
        await _record_invocation(
            db,
            user=user,
            template=template,
            tier=tier,
            provider_name=provider.name,
            model=provider.model,
            tokens_in=0,
            tokens_out=0,
            cost_minor=0,
            latency_ms=0.0,
            cached=False,
            fallback_used=False,
            outcome="quota_denied",
            correlation_id=correlation_id,
        )
        raise

    async def _deny(outcome: Outcome) -> None:
        await release(db, reservation)
        await _record_invocation(
            db,
            user=user,
            template=template,
            tier=tier,
            provider_name=provider.name,
            model=provider.model,
            tokens_in=0,
            tokens_out=0,
            cost_minor=0,
            latency_ms=0.0,
            cached=False,
            fallback_used=False,
            outcome=outcome,
            correlation_id=correlation_id,
        )

    rendered = render_prompt(template, sanitized_context)
    request = LLMRequest(
        messages=_build_messages(rendered),
        tier=tier,
        correlation_id=correlation_id,
        prompt_id=template.id,
        prompt_version=template.version,
        response_schema=template.output_schema,
        max_output_tokens=template.max_output_tokens,
        temperature=template.temperature,
    )

    started = time.monotonic()
    try:
        # 5. Call the provider (retry + fallback)
        response, fallback_used = await _call_with_fallback(provider, request, tier=tier)
    except AIProviderUnavailable:
        await _deny("provider_error")
        raise

    # 6. Schema validation + exactly one repair attempt
    parsed: Any = None
    if template.output_schema is not None:
        valid, parsed = _validate_against_schema(
            text=response.text, parsed=response.parsed, schema=template.output_schema
        )
        if not valid:
            try:
                repair_response = await asyncio.wait_for(
                    provider.complete(
                        _repair_request(request, response.text or "", template.output_schema)
                    ),
                    timeout=registry.tier_timeout_seconds(tier),
                )
            except (ProviderError, TimeoutError):
                await _deny("invalid_output")
                raise AIOutputInvalid(template.id) from None
            valid, parsed = _validate_against_schema(
                text=repair_response.text,
                parsed=repair_response.parsed,
                schema=template.output_schema,
            )
            if not valid:
                await _deny("invalid_output")
                raise AIOutputInvalid(template.id)
            response = repair_response

    # 7. Output policy
    try:
        check_output_policy(response.text or "")
    except OutputPolicyViolation:
        await _deny("policy_blocked")
        raise

    latency_ms = (time.monotonic() - started) * 1000
    cost_minor = _estimate_cost_minor(
        model=response.model, tokens_in=response.tokens_in, tokens_out=response.tokens_out
    )

    # 8. Record + cache
    invocation = await _record_invocation(
        db,
        user=user,
        template=template,
        tier=tier,
        provider_name=response.provider,
        model=response.model,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        cost_minor=cost_minor,
        latency_ms=latency_ms,
        cached=False,
        fallback_used=fallback_used,
        outcome="ok",
        correlation_id=correlation_id,
    )
    await _store_cache_entry(
        db,
        cache_key=cache_key,
        prompt_id=template.id,
        prompt_version=template.version,
        text=response.text,
        parsed=parsed,
        tokens=response.tokens_out,
        ttl_seconds=template.cache_ttl_seconds,
    )

    return GatewayResult(
        text=response.text,
        parsed=parsed,
        model=response.model,
        provider=response.provider,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        cost_minor=cost_minor,
        currency=registry.currency(),
        latency_ms=latency_ms,
        cached=False,
        fallback_used=fallback_used,
        correlation_id=correlation_id,
        invocation_id=invocation.id,
    )


async def _stream(
    prompt_id: str,
    context: Mapping[str, Any],
    *,
    user: User,
    db: AsyncSession,
    tier_override: ModelTier | None,
    idempotency_key: str | None,
) -> AsyncIterator[dict[str, Any]]:
    """Same pipeline as `_complete`, but frames go out as they arrive and
    validation (schema + output policy) happens only once the stream ends
    — there is no mid-stream repair call, since repairing would mean
    silently discarding tokens already shown to the client. An invalid or
    policy-blocked ending is reported as an `error` frame after the fact
    and recorded with the matching outcome; the client has still seen the
    (unvalidated) text by then, which is the accepted tradeoff of
    streaming raw deltas rather than a single validated response."""
    correlation_id = idempotency_key or str(uuid.uuid4())
    try:
        template = get_prompt(prompt_id)
    except ApiError as exc:
        yield {"type": "error", "code": exc.code.value, "message": exc.message}
        return
    tier = tier_override or template.tier

    try:
        validate_required_context(template, context)
    except ApiError as exc:
        yield {"type": "error", "code": exc.code.value, "message": exc.message}
        return

    sanitized_context = sanitize_context(context)
    provider = registry.resolve_provider(tier, user.plan)
    cache_key = compute_cache_key(
        prompt_id=template.id,
        version=template.version,
        context=context,
        tier=tier,
        model=provider.model,
    )

    cached_entry = await _get_cache_entry(db, cache_key)
    if cached_entry is not None:
        payload = cached_entry.response
        text = payload.get("text") or ""
        yield {
            "type": "meta",
            "correlation_id": correlation_id,
            "model": provider.model,
            "provider": provider.name,
            "cached": True,
        }
        if text:
            yield {"type": "delta", "text": text}
        await _record_invocation(
            db,
            user=user,
            template=template,
            tier=tier,
            provider_name=provider.name,
            model=provider.model,
            tokens_in=0,
            tokens_out=cached_entry.tokens,
            cost_minor=0,
            latency_ms=0.0,
            cached=True,
            fallback_used=False,
            outcome="ok",
            correlation_id=correlation_id,
        )
        yield {"type": "done", "tokens_in": 0, "tokens_out": cached_entry.tokens, "cost_minor": 0}
        return

    try:
        reservation = await check_and_reserve(db, user=user, metric="ai_runs")
    except ApiError as exc:
        yield {"type": "error", "code": exc.code.value, "message": exc.message}
        return

    rendered = render_prompt(template, sanitized_context)
    request = LLMRequest(
        messages=_build_messages(rendered),
        tier=tier,
        correlation_id=correlation_id,
        prompt_id=template.id,
        prompt_version=template.version,
        response_schema=template.output_schema,
        max_output_tokens=template.max_output_tokens,
        temperature=template.temperature,
    )

    yield {
        "type": "meta",
        "correlation_id": correlation_id,
        "model": provider.model,
        "provider": provider.name,
        "cached": False,
    }

    text_parts: list[str] = []
    tokens_in = 0
    tokens_out = 0
    model_used = provider.model
    provider_used = provider.name
    started = time.monotonic()
    try:
        async with aclosing(provider.stream(request)) as chunks:
            async for chunk in chunks:
                if chunk.delta:
                    text_parts.append(chunk.delta)
                    yield {"type": "delta", "text": chunk.delta}
                if chunk.done:
                    tokens_in = chunk.tokens_in or 0
                    tokens_out = chunk.tokens_out or 0
                    model_used = chunk.model or model_used
                    provider_used = chunk.provider or provider_used
    except (ProviderError, TimeoutError):
        await release(db, reservation)
        await _record_invocation(
            db,
            user=user,
            template=template,
            tier=tier,
            provider_name=provider.name,
            model=provider.model,
            tokens_in=0,
            tokens_out=0,
            cost_minor=0,
            latency_ms=0.0,
            cached=False,
            fallback_used=False,
            outcome="provider_error",
            correlation_id=correlation_id,
        )
        yield {
            "type": "error",
            "code": ErrorCode.AI_PROVIDER_UNAVAILABLE.value,
            "message": "the provider stream failed",
        }
        return

    full_text = "".join(text_parts)
    latency_ms = (time.monotonic() - started) * 1000

    outcome: Outcome = "ok"
    parsed: Any = None
    if template.output_schema is not None:
        valid, parsed = _validate_against_schema(
            text=full_text, parsed=None, schema=template.output_schema
        )
        if not valid:
            outcome = "invalid_output"

    if outcome == "ok":
        try:
            check_output_policy(full_text)
        except OutputPolicyViolation:
            outcome = "policy_blocked"

    cost_minor = _estimate_cost_minor(model=model_used, tokens_in=tokens_in, tokens_out=tokens_out)

    if outcome != "ok":
        await release(db, reservation)
        await _record_invocation(
            db,
            user=user,
            template=template,
            tier=tier,
            provider_name=provider_used,
            model=model_used,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_minor=cost_minor,
            latency_ms=latency_ms,
            cached=False,
            fallback_used=provider_used != provider.name,
            outcome=outcome,
            correlation_id=correlation_id,
        )
        code = (
            ErrorCode.AI_OUTPUT_INVALID
            if outcome == "invalid_output"
            else ErrorCode.AI_POLICY_BLOCKED
        )
        yield {
            "type": "error",
            "code": code.value,
            "message": f"stream ended with outcome {outcome!r}",
        }
        return

    await _record_invocation(
        db,
        user=user,
        template=template,
        tier=tier,
        provider_name=provider_used,
        model=model_used,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_minor=cost_minor,
        latency_ms=latency_ms,
        cached=False,
        fallback_used=provider_used != provider.name,
        outcome="ok",
        correlation_id=correlation_id,
    )
    await _store_cache_entry(
        db,
        cache_key=cache_key,
        prompt_id=template.id,
        prompt_version=template.version,
        text=full_text,
        parsed=parsed,
        tokens=tokens_out,
        ttl_seconds=template.cache_ttl_seconds,
    )

    yield {
        "type": "done",
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_minor": cost_minor,
        "latency_ms": latency_ms,
        "fallback_used": provider_used != provider.name,
    }


def run(
    prompt_id: str,
    context: Mapping[str, Any],
    *,
    user: User,
    db: AsyncSession,
    tier_override: ModelTier | None = None,
    stream: bool = False,
    idempotency_key: str | None = None,
) -> Any:
    """`await`ed when `stream=False` (returns a `GatewayResult`); iterated
    with `async for` when `stream=True` (yields SSE-shaped frame dicts).
    A plain `def` on purpose — which of those two things calling this
    returns depends on `stream`, decided before any `async` machinery
    starts, so the caller never has to `await` before it can iterate."""
    if stream:
        return _stream(
            prompt_id,
            context,
            user=user,
            db=db,
            tier_override=tier_override,
            idempotency_key=idempotency_key,
        )
    return _complete(
        prompt_id,
        context,
        user=user,
        db=db,
        tier_override=tier_override,
        idempotency_key=idempotency_key,
    )
