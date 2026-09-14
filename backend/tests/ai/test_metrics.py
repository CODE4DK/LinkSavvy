from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.metrics import compute_metrics
from app.models.ai_invocation import AIInvocation
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"metrics-{uuid.uuid4()}@example.com", full_name="Metrics Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _invocation(
    *,
    user_id: uuid.UUID,
    latency_ms: int,
    cached: bool,
    fallback_used: bool,
    outcome: str,
    cost_minor: int,
) -> AIInvocation:
    return AIInvocation(
        user_id=user_id,
        prompt_id="text.summarise.v1",
        prompt_version=1,
        tier="fast",
        provider="fake",
        model="fake-model",
        tokens_in=10,
        tokens_out=5,
        cost_minor=cost_minor,
        currency="USD",
        latency_ms=latency_ms,
        cached=cached,
        fallback_used=fallback_used,
        outcome=outcome,
        correlation_id=str(uuid.uuid4()),
    )


async def test_empty_window_returns_none_rates(db_session: AsyncSession) -> None:
    metrics = await compute_metrics(db_session, window_hours=24)
    assert metrics.total_invocations == 0
    assert metrics.latency_p50_ms is None
    assert metrics.latency_p95_ms is None
    assert metrics.cache_hit_rate is None
    assert metrics.fallback_rate is None
    assert metrics.invalid_output_rate is None
    assert metrics.cost_per_user_per_day_minor == {}


async def test_latency_percentiles_and_rates(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    latencies = [10, 20, 30, 40, 100]
    for i, latency in enumerate(latencies):
        db_session.add(
            _invocation(
                user_id=user.id,
                latency_ms=latency,
                cached=(i == 0),
                fallback_used=(i == 1),
                outcome="invalid_output" if i == 2 else "ok",
                cost_minor=100,
            )
        )
    await db_session.commit()

    metrics = await compute_metrics(db_session, window_hours=24)
    assert metrics.total_invocations == 5
    assert metrics.latency_p50_ms == 30
    assert metrics.cache_hit_rate == 1 / 5
    assert metrics.fallback_rate == 1 / 5
    assert metrics.invalid_output_rate == 1 / 5


async def test_cost_is_grouped_per_user_per_day(db_session: AsyncSession) -> None:
    user_a = await _create_user(db_session)
    user_b = await _create_user(db_session)
    db_session.add(
        _invocation(
            user_id=user_a.id,
            latency_ms=10,
            cached=False,
            fallback_used=False,
            outcome="ok",
            cost_minor=100,
        )
    )
    db_session.add(
        _invocation(
            user_id=user_a.id,
            latency_ms=10,
            cached=False,
            fallback_used=False,
            outcome="ok",
            cost_minor=50,
        )
    )
    db_session.add(
        _invocation(
            user_id=user_b.id,
            latency_ms=10,
            cached=False,
            fallback_used=False,
            outcome="ok",
            cost_minor=25,
        )
    )
    await db_session.commit()

    metrics = await compute_metrics(db_session, window_hours=24)
    today = datetime.now(UTC).date().isoformat()
    assert metrics.cost_per_user_per_day_minor[f"{user_a.id}:{today}"] == 150
    assert metrics.cost_per_user_per_day_minor[f"{user_b.id}:{today}"] == 25


async def test_invocations_outside_window_are_excluded(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    old = _invocation(
        user_id=user.id,
        latency_ms=999,
        cached=False,
        fallback_used=False,
        outcome="ok",
        cost_minor=1,
    )
    old.created_at = datetime.now(UTC) - timedelta(hours=48)
    db_session.add(old)
    await db_session.commit()

    metrics = await compute_metrics(db_session, window_hours=24)
    assert metrics.total_invocations == 0
