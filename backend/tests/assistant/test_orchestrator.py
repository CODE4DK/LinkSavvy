from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.assistant import conversations as conversations_service
from app.assistant import orchestrator
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"orchestrator-{uuid.uuid4()}@example.com", full_name="Orchestrator Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _fake_gateway_result(parsed: dict[str, Any]) -> gateway.GatewayResult:
    return gateway.GatewayResult(
        text=None,
        parsed=parsed,
        model="fake-model",
        provider="fake",
        tokens_in=1,
        tokens_out=1,
        cost_minor=0,
        currency="usd",
        latency_ms=0.0,
        cached=False,
        fallback_used=False,
        correlation_id=str(uuid.uuid4()),
        invocation_id=uuid.uuid4(),
    )


def _classification(**overrides: Any) -> dict[str, Any]:
    base = {
        "intent": "explain",
        "tool_candidates": [],
        "confidence": 0.9,
        "needs_context": [],
        "policy_category": None,
    }
    base.update(overrides)
    return base


def _reply(**overrides: Any) -> dict[str, Any]:
    base = {"reply": "Here's an answer.", "proposed_tool": None}
    base.update(overrides)
    return base


def _tool_call(message: Any) -> dict[str, Any]:
    assert message.tool_call is not None
    return dict(message.tool_call)


def _sequenced_gateway(monkeypatch: pytest.MonkeyPatch, *parsed_payloads: dict[str, Any]) -> None:
    """Patches gateway.run to return each payload in order, one per call
    -- the classifier call first, then the reply call, matching
    orchestrator's own call sequence for an auto/tool-mode turn."""
    payloads = iter(parsed_payloads)

    async def _fake_run(*args: Any, **kwargs: Any) -> gateway.GatewayResult:
        return _fake_gateway_result(next(payloads))

    monkeypatch.setattr(gateway, "run", _fake_run)


async def test_handle_message_explain_intent_produces_a_reply(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(
        monkeypatch, _classification(intent="explain"), _reply(reply="Here's how that works.")
    )

    result = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="How does the Health Score work?"
    )

    assert result.message.role == "assistant"
    assert result.message.content == "Here's how that works."
    assert _tool_call(result.message)["intent"] == "explain"
    assert result.quota.used == 1


async def test_handle_message_input_policy_refusal_skips_the_gateway(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)

    calls = 0

    async def _fake_run(*args: Any, **kwargs: Any) -> gateway.GatewayResult:
        nonlocal calls
        calls += 1
        return _fake_gateway_result(_classification())

    monkeypatch.setattr(gateway, "run", _fake_run)

    result = await orchestrator.handle_message(
        db_session,
        user=user,
        conversation=conversation,
        text="Can you auto-connect with everyone in this list?",
    )

    assert calls == 0  # never reached the gateway at all
    assert "can't help automate" in result.message.content
    assert _tool_call(result.message)["intent"] == "policy_violation"


async def test_handle_message_out_of_scope_intent_is_a_canned_redirect(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(monkeypatch, _classification(intent="out_of_scope"))

    result = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="What's the capital of France?"
    )

    assert "outside what I help with" in result.message.content


async def test_handle_message_classifier_policy_violation_uses_category_refusal(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(
        monkeypatch,
        _classification(intent="policy_violation", policy_category="fabrication"),
    )

    result = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="something subtly fabricated"
    )

    assert "invent credentials" in result.message.content


async def test_handle_message_rejects_a_proposed_tool_outside_candidates(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(
        monkeypatch,
        _classification(intent="run_tool", tool_candidates=["profile.headline_optimizer"]),
        _reply(
            proposed_tool={
                "tool_id": "content.post_generator",  # not in tool_candidates
                "reasoning": "sneaky",
                "prefilled_input": {},
            }
        ),
    )

    result = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="Fix my headline"
    )

    assert _tool_call(result.message)["proposed_tool"] is None


async def test_handle_message_accepts_a_valid_proposed_tool(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(
        monkeypatch,
        _classification(intent="run_tool", tool_candidates=["profile.headline_optimizer"]),
        _reply(
            proposed_tool={
                "tool_id": "profile.headline_optimizer",
                "reasoning": "This tool rewrites headlines.",
                "prefilled_input": {"target_role": "Staff Engineer"},
            }
        ),
    )

    result = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="Fix my headline for Staff Engineer"
    )

    proposed = _tool_call(result.message)["proposed_tool"]
    assert proposed["tool_id"] == "profile.headline_optimizer"


async def test_pinned_tool_mode_skips_classification_entirely(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(
        db_session,
        user=user,
        mode="tool",
        context_snapshot={"pinned_tool_id": "profile.headline_optimizer"},
    )

    call_count = 0

    async def _fake_run(prompt_id: str, *args: Any, **kwargs: Any) -> gateway.GatewayResult:
        nonlocal call_count
        call_count += 1
        assert prompt_id == "assistant.reply.v1"  # never calls the classifier
        return _fake_gateway_result(_reply())

    monkeypatch.setattr(gateway, "run", _fake_run)

    result = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="Make it punchier"
    )

    assert call_count == 1
    assert _tool_call(result.message)["intent"] == "run_tool"


async def test_retry_message_creates_a_sibling_reply(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(monkeypatch, _classification(), _reply(reply="First answer"))
    first = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="Help me"
    )
    user_message_id = first.message.parent_message_id
    assert user_message_id is not None

    _sequenced_gateway(monkeypatch, _classification(), _reply(reply="Second answer"))
    retried = await orchestrator.retry_message(
        db_session,
        user=user,
        conversation=conversation,
        user_message_id=user_message_id,
    )

    assert retried.message.content == "Second answer"
    assert retried.message.parent_message_id == user_message_id
    assert retried.message.id != first.message.id


async def test_edit_and_branch_creates_a_new_user_message_and_reply(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(monkeypatch, _classification(), _reply(reply="Original answer"))
    first = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="Original question"
    )
    original_user_message_id = first.message.parent_message_id
    assert original_user_message_id is not None

    _sequenced_gateway(monkeypatch, _classification(), _reply(reply="Edited answer"))
    edited = await orchestrator.edit_and_branch(
        db_session,
        user=user,
        conversation=conversation,
        message_id=original_user_message_id,
        new_text="Edited question",
    )

    assert edited.message.content == "Edited answer"

    all_messages = await conversations_service.list_messages(
        db_session, conversation_id=conversation.id
    )
    user_messages = [m for m in all_messages if m.role == "user"]
    assert {m.content for m in user_messages} == {"Original question", "Edited question"}


async def test_rate_message_stores_the_rating_without_clobbering_tool_call(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await _create_user(db_session)
    conversation = await conversations_service.create_conversation(db_session, user=user)
    _sequenced_gateway(monkeypatch, _classification(intent="smalltalk"), _reply(reply="Hi there!"))
    result = await orchestrator.handle_message(
        db_session, user=user, conversation=conversation, text="hey"
    )

    rated = await orchestrator.rate_message(
        db_session,
        user=user,
        conversation_id=conversation.id,
        message_id=result.message.id,
        rating="up",
    )

    assert _tool_call(rated)["rating"] == "up"
    assert _tool_call(rated)["intent"] == "smalltalk"
