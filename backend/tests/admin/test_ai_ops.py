from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import ai_ops
from app.models.ai_invocation import AIInvocation
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"aiops-{uuid.uuid4()}@example.com", full_name="AI Ops Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _seed_invocation(db: AsyncSession, *, user: User, **overrides: object) -> None:
    defaults: dict[str, object] = dict(
        user_id=user.id,
        prompt_id="profile.headline_optimizer.v1",
        prompt_version=1,
        tier="standard",
        provider="openai",
        model="gpt-test",
        tokens_in=100,
        tokens_out=200,
        cost_minor=50,
        currency="USD",
        latency_ms=800,
        cached=False,
        fallback_used=False,
        outcome="ok",
        correlation_id=str(uuid.uuid4()),
    )
    defaults.update(overrides)
    db.add(AIInvocation(**defaults))
    await db.commit()


async def test_cost_by_day_aggregates_todays_spend(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_invocation(db_session, user=user, cost_minor=100)
    await _seed_invocation(db_session, user=user, cost_minor=50)

    days = await ai_ops.cost_by_day(db_session)
    assert len(days) == 1
    assert days[0].cost_minor == 150
    assert days[0].invocation_count == 2


async def test_cost_by_model_and_prompt(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_invocation(db_session, user=user, model="gpt-a", prompt_id="prompt.a")
    await _seed_invocation(db_session, user=user, model="gpt-b", prompt_id="prompt.b")

    by_model = await ai_ops.cost_by_model(db_session)
    assert {row.key for row in by_model} == {"gpt-a", "gpt-b"}

    by_prompt = await ai_ops.cost_by_prompt(db_session)
    assert {row.key for row in by_prompt} == {"prompt.a", "prompt.b"}


async def test_outcome_rates_computes_fractions(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_invocation(db_session, user=user, outcome="ok")
    await _seed_invocation(db_session, user=user, outcome="invalid_output")
    await _seed_invocation(db_session, user=user, outcome="ok", fallback_used=True)

    rates = await ai_ops.outcome_rates(db_session)
    assert rates.total == 3
    assert round(rates.invalid_output_rate, 2) == round(1 / 3, 2)
    assert round(rates.fallback_rate, 2) == round(1 / 3, 2)


async def test_slowest_prompts_ranks_by_latency(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_invocation(db_session, user=user, prompt_id="fast.prompt", latency_ms=100)
    await _seed_invocation(db_session, user=user, prompt_id="slow.prompt", latency_ms=5000)

    slow = await ai_ops.slowest_prompts(db_session)
    assert slow[0].prompt_id == "slow.prompt"


async def test_prompt_drilldown_returns_matching_invocations(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_invocation(db_session, user=user, prompt_id="target.prompt")
    await _seed_invocation(db_session, user=user, prompt_id="other.prompt")

    rows = await ai_ops.prompt_drilldown(db_session, prompt_id="target.prompt")
    assert len(rows) == 1
    assert rows[0].prompt_id == "target.prompt"
