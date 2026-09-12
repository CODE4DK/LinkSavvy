"""Golden tests for the three seed prompts against the real registry and
the fixture-driven FakeProvider — end to end through gateway.run(), with
no monkeypatching of get_prompt. Each fixture in
app/ai/providers/fake_fixtures/<prompt_id>.json is the exact canned
output asserted against here, so a change to either the prompt's
required_context or the fixture shape fails loudly.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.ai.providers.fake_provider import DEFAULT_FIXTURES_DIR
from app.models.user import User


def _load_fixture(prompt_id: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((DEFAULT_FIXTURES_DIR / f"{prompt_id}.json").read_text())
    return result


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"golden-{uuid.uuid4()}@example.com", full_name="Golden Tester", plan="free")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_profile_headline_v1_golden(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    result = await gateway.run(
        "profile.headline.v1",
        {
            "profile_summary": "Senior backend engineer with 8 years building distributed systems.",
            "target_role": "Staff Engineer",
        },
        user=user,
        db=db_session,
    )
    fixture = _load_fixture("profile.headline.v1")
    assert result.parsed == fixture["response"]
    assert result.cached is False
    assert result.provider == "fake"  # tests always run against FakeProvider


async def test_text_summarise_v1_golden(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    result = await gateway.run(
        "text.summarise.v1",
        {"text": "A long block of profile text describing an engineer's career."},
        user=user,
        db=db_session,
    )
    fixture = _load_fixture("text.summarise.v1")
    assert result.text == fixture["response"]["text"]
    assert result.parsed is None


async def test_meta_classify_intent_v1_golden(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    result = await gateway.run(
        "meta.classify_intent.v1",
        {"message": "Can you make my headline sound more senior?"},
        user=user,
        db=db_session,
    )
    fixture = _load_fixture("meta.classify_intent.v1")
    assert result.parsed == fixture["response"]
    assert result.parsed["intent"] == "rewrite_headline"


async def test_meta_classify_intent_v1_is_never_cached(db_session: AsyncSession) -> None:
    """cache_ttl_seconds: 0 in the prompt's frontmatter -- confirm two
    identical calls both hit the (fake) provider rather than the cache."""
    user = await _create_user(db_session)
    first = await gateway.run(
        "meta.classify_intent.v1", {"message": "same message"}, user=user, db=db_session
    )
    second = await gateway.run(
        "meta.classify_intent.v1", {"message": "same message"}, user=user, db=db_session
    )
    assert first.cached is False
    assert second.cached is False


async def test_profile_headline_v1_is_cached_on_second_call(db_session: AsyncSession) -> None:
    """cache_ttl_seconds: 86400 -- confirm the second identical call is a
    cache hit, unlike the never-cached intent classifier above."""
    user = await _create_user(db_session)
    context = {"profile_summary": "Same profile text.", "target_role": "Staff Engineer"}
    first = await gateway.run("profile.headline.v1", context, user=user, db=db_session)
    second = await gateway.run("profile.headline.v1", context, user=user, db=db_session)
    assert first.cached is False
    assert second.cached is True


def test_every_seed_prompt_has_a_fake_provider_fixture() -> None:
    for prompt_id in ("profile.headline.v1", "text.summarise.v1", "meta.classify_intent.v1"):
        assert (DEFAULT_FIXTURES_DIR / f"{prompt_id}.json").is_file()
