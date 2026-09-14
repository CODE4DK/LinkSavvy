"""The AI Assistant's turn-by-turn orchestration, built on the Phase 3
gateway. A `coach`-mode conversation is handled entirely by the absorbed
Growth Coach (app.growth.coach) -- everything below is for `auto`/`tool`
conversations: a cheap fast-tier intent classification, context assembly
(reusing app.tools.context's assembler with a larger budget), and either
a tool proposal or a direct reply, never a tool run itself -- that only
ever happens once the user clicks Run (see `confirm_and_run_tool`).

Editing a user message and retrying an assistant reply are the same
underlying operation -- generate a fresh assistant reply as a *sibling*
branch under a fixed parent, never overwriting history (see
app/assistant/conversations.py's `get_thread`) -- so both go through the
one `_generate_assistant_reply` core.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.moderation import flag_ai_policy_violation
from app.ai import gateway
from app.ai.providers.base import ModelTier
from app.assistant import policy, reads
from app.assistant.conversations import append_message, get_owned_message, get_thread
from app.assistant.presenters import to_message_response, to_quota_info
from app.assistant.summarize import conversation_history_text
from app.billing.quota import QuotaStatus, check_and_reserve, peek, release
from app.errors import ApiError, ErrorCode
from app.models.ai_invocation import AIInvocation
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.tools import service as tools_service
from app.tools.context import ContextKey, assemble
from app.tools.registry import get_tool

ASSISTANT_MESSAGES_METRIC = "assistant_messages"
ASSISTANT_TOKEN_BUDGET = 12000

# Every optional context key the "what I can see" panel can toggle.
# None of these are `required` -- a fresh user with no audit, no goal, or
# no saved assets yet still gets a working conversation; assemble() simply
# omits whatever it has nothing to serialize for.
ALL_CONTEXT_KEYS = [
    ContextKey.PROFILE_IDENTITY,
    ContextKey.PROFILE_HEADLINE,
    ContextKey.AUDIT_SUMMARY,
    ContextKey.GROWTH_GOAL,
    ContextKey.RECENT_ASSET_TITLES,
]

_TIER_BY_INTENT: dict[str, ModelTier] = {
    "smalltalk": ModelTier.FAST,
    "explain": ModelTier.STANDARD,
    "run_tool": ModelTier.STANDARD,
    "analyse_my_data": ModelTier.ADVANCED,
}

_OUT_OF_SCOPE_REPLY = (
    "That's outside what I help with -- I'm focused on your LinkedIn profile, "
    "content, engagement, career materials, and growth. Happy to dig into any "
    "of those instead."
)

_COACH_REDIRECT_REPLY = (
    "It sounds like you want ongoing, goal-oriented coaching -- that's what the "
    "Growth Coach is for. Head to the Growth Hub and open the Coach; I'll pick "
    "up there with your real scores and history."
)

_GENERIC_POLICY_REFUSAL = (
    "I can't help with that -- it would mean automating, manipulating, or "
    "misrepresenting something on LinkedIn, which LinkSavvy doesn't do. Let me "
    "know what you're actually trying to achieve and I'll suggest a compliant "
    "way to get there."
)

_ACTION_CLAIM_FALLBACK = (
    "I can only propose a tool run for you to review and confirm -- I haven't "
    "taken any action on LinkedIn, and I never will on my own. Review the "
    "details above and click Run yourself when you're ready."
)

_QUOTA_WARNING_THRESHOLD = 0.8


class UnknownConversationMode(Exception):
    pass


@dataclass(frozen=True, slots=True)
class TurnResult:
    message: Message
    quota: QuotaStatus
    quota_warning: str | None


def excluded_context_keys(conversation: Conversation) -> set[str]:
    return set((conversation.context_snapshot or {}).get("excluded_context_keys") or [])


def _available_context_keys(conversation: Conversation) -> list[ContextKey]:
    excluded = excluded_context_keys(conversation)
    return [key for key in ALL_CONTEXT_KEYS if key.value not in excluded]


async def assemble_context_for_conversation(
    db: AsyncSession, *, user: User, conversation: Conversation
) -> tuple[str, list[ContextKey]]:
    optional = _available_context_keys(conversation)
    context, included = await assemble(
        db=db, user=user, required=[], optional=optional, token_budget=ASSISTANT_TOKEN_BUDGET
    )
    text = "\n\n".join(context.values()) if context else "(no additional context available yet)"
    return text, included


def _quota_warning(quota: QuotaStatus) -> str | None:
    if quota.limit <= 0 or quota.used / quota.limit < _QUOTA_WARNING_THRESHOLD:
        return None
    remaining = max(0, quota.limit - quota.used)
    return (
        f"You're approaching your daily assistant message limit ({quota.used}/{quota.limit}) "
        f"-- {remaining} left before it resets."
    )


async def _classify_intent(
    db: AsyncSession, *, user: User, history_text: str, text: str
) -> dict[str, Any]:
    available_tools = await reads.list_available_tools(db, user=user)
    context = {
        "available_tools": available_tools,
        "conversation_history": history_text,
        "user_message": text,
    }
    result = await gateway.run("assistant.intent_classifier.v1", context, user=user, db=db)
    assert result.parsed is not None
    return dict(result.parsed)


def _pinned_tool_id(conversation: Conversation) -> str | None:
    snapshot = conversation.context_snapshot or {}
    value = snapshot.get("pinned_tool_id")
    return value if isinstance(value, str) else None


async def _build_reply_context(
    db: AsyncSession,
    *,
    user: User,
    conversation: Conversation,
    user_message: Message,
    history_text: str,
    text: str,
    intent: str,
    tool_candidates: list[str],
    needs_context: list[str],
) -> tuple[dict[str, str], ModelTier]:
    """Everything a reply generation call needs, short of actually
    calling the gateway -- shared by the non-streaming and streaming
    paths (`_reply_turn` and `stream_message`) so context assembly and
    the on-demand `search_my_workspace` read only happen once each."""
    extra_blocks: list[str] = []
    if "workspace" in needs_context:
        result = await reads.search_my_workspace(db, user=user, query=text)
        extra_blocks.append(f"## Workspace search results for {text!r}\n{result}")
        await append_message(
            db,
            conversation=conversation,
            role="tool",
            content=result,
            tool_call={"tool": "search_my_workspace", "query": text},
            parent_message_id=user_message.id,
        )

    user_context_text, _included = await assemble_context_for_conversation(
        db, user=user, conversation=conversation
    )
    if extra_blocks:
        user_context_text = "\n\n".join([user_context_text, *extra_blocks])

    tier = _TIER_BY_INTENT.get(intent, ModelTier.STANDARD)
    context = {
        "intent": intent,
        "tool_candidates": ", ".join(tool_candidates) if tool_candidates else "(none)",
        "user_context": user_context_text,
        "conversation_history": history_text,
        "user_message": text,
    }
    return context, tier


async def _finalize_reply(
    db: AsyncSession,
    parsed: dict[str, Any],
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    tool_candidates: list[str],
) -> tuple[str, dict[str, Any] | None]:
    reply_text = parsed["reply"]
    violations = policy.check_output(reply_text)
    if violations:
        await flag_ai_policy_violation(
            db,
            user_id=user_id,
            target_type="conversation",
            target_id=str(conversation_id),
            reason=f"output policy: {', '.join(violations)}",
            content=reply_text,
        )
    if "action_claim" in violations:
        reply_text = _ACTION_CLAIM_FALLBACK

    proposed_tool = parsed.get("proposed_tool")
    if proposed_tool is not None:
        if proposed_tool["tool_id"] not in tool_candidates:
            # The model proposed something outside the vetted candidate
            # list the classifier produced -- never trust that blindly.
            proposed_tool = None
        else:
            get_tool(proposed_tool["tool_id"])  # 404s loudly if the id is somehow stale
    return reply_text, proposed_tool


async def _reply_turn(
    db: AsyncSession,
    *,
    user: User,
    conversation: Conversation,
    user_message: Message,
    history_text: str,
    text: str,
    intent: str,
    tool_candidates: list[str],
    needs_context: list[str],
) -> Message:
    context, tier = await _build_reply_context(
        db,
        user=user,
        conversation=conversation,
        user_message=user_message,
        history_text=history_text,
        text=text,
        intent=intent,
        tool_candidates=tool_candidates,
        needs_context=needs_context,
    )
    result = await gateway.run("assistant.reply.v1", context, user=user, db=db, tier_override=tier)
    assert result.parsed is not None
    reply_text, proposed_tool = await _finalize_reply(
        db,
        dict(result.parsed),
        user_id=user.id,
        conversation_id=conversation.id,
        tool_candidates=tool_candidates,
    )

    return await append_message(
        db,
        conversation=conversation,
        role="assistant",
        content=reply_text,
        ai_invocation_id=result.invocation_id,
        parent_message_id=user_message.id,
        tool_call={"intent": intent, "proposed_tool": proposed_tool},
        tokens=result.tokens_out,
    )


async def _generate_assistant_reply(
    db: AsyncSession,
    *,
    user: User,
    conversation: Conversation,
    user_message: Message,
    history_before_text: str,
) -> Message:
    text = user_message.content

    refusal = policy.check_input(text)
    if refusal is not None:
        return await append_message(
            db,
            conversation=conversation,
            role="assistant",
            content=refusal.message,
            parent_message_id=user_message.id,
            tool_call={"intent": "policy_violation", "policy_category": refusal.category},
        )

    pinned_tool_id = _pinned_tool_id(conversation) if conversation.mode == "tool" else None
    if pinned_tool_id is not None:
        intent, tool_candidates, needs_context, policy_category = (
            "run_tool",
            [pinned_tool_id],
            [],
            None,
        )
    else:
        classification = await _classify_intent(
            db, user=user, history_text=history_before_text, text=text
        )
        intent = classification["intent"]
        tool_candidates = list(classification.get("tool_candidates") or [])
        needs_context = list(classification.get("needs_context") or [])
        policy_category = classification.get("policy_category")

    if intent == "policy_violation":
        message = policy.refusal_message_for_category(
            policy_category, fallback=_GENERIC_POLICY_REFUSAL
        )
        return await append_message(
            db,
            conversation=conversation,
            role="assistant",
            content=message,
            parent_message_id=user_message.id,
            tool_call={"intent": intent, "policy_category": policy_category},
        )

    if intent == "out_of_scope":
        return await append_message(
            db,
            conversation=conversation,
            role="assistant",
            content=_OUT_OF_SCOPE_REPLY,
            parent_message_id=user_message.id,
            tool_call={"intent": intent},
        )

    if intent == "coach":
        return await append_message(
            db,
            conversation=conversation,
            role="assistant",
            content=_COACH_REDIRECT_REPLY,
            parent_message_id=user_message.id,
            tool_call={"intent": intent},
        )

    return await _reply_turn(
        db,
        user=user,
        conversation=conversation,
        user_message=user_message,
        history_text=history_before_text,
        text=text,
        intent=intent,
        tool_candidates=tool_candidates,
        needs_context=needs_context,
    )


async def _with_assistant_quota(
    db: AsyncSession, *, user: User, generate: Callable[[], Awaitable[Message]]
) -> TurnResult:
    reservation = await check_and_reserve(db, user=user, metric=ASSISTANT_MESSAGES_METRIC)
    try:
        message = await generate()
    except Exception:
        await release(db, reservation)
        raise
    quota = await peek(db, user=user, metric=ASSISTANT_MESSAGES_METRIC)
    return TurnResult(message=message, quota=quota, quota_warning=_quota_warning(quota))


async def handle_message(
    db: AsyncSession, *, user: User, conversation: Conversation, text: str
) -> TurnResult:
    """The entrypoint for a brand new user message, whatever the
    conversation's mode. Enforces the `assistant_messages` quota once per
    user message here -- not per internal gateway call, which the
    gateway's own `ai_runs` quota already meters independently."""

    async def _generate() -> Message:
        if conversation.mode == "coach":
            from app.growth import coach as growth_coach

            return await growth_coach.send_message(
                db, user=user, conversation=conversation, text=text
            )
        if conversation.mode not in ("auto", "tool"):
            raise UnknownConversationMode(conversation.mode)

        thread = await get_thread(db, conversation_id=conversation.id)
        prior_leaf_id = thread[-1].id if thread else None
        history_text = conversation_history_text(thread)
        user_message = await append_message(
            db,
            conversation=conversation,
            role="user",
            content=text,
            parent_message_id=prior_leaf_id,
        )
        return await _generate_assistant_reply(
            db,
            user=user,
            conversation=conversation,
            user_message=user_message,
            history_before_text=history_text,
        )

    return await _with_assistant_quota(db, user=user, generate=_generate)


async def retry_message(
    db: AsyncSession, *, user: User, conversation: Conversation, user_message_id: uuid.UUID
) -> TurnResult:
    """Regenerates the assistant's reply to an existing user message as a
    new sibling branch -- the original reply stays in history."""

    async def _generate() -> Message:
        user_message = await get_owned_message(
            db, user_id=user.id, conversation_id=conversation.id, message_id=user_message_id
        )
        if user_message.role != "user":
            raise ApiError(ErrorCode.VALIDATION_FAILED, "only a user message can be retried")
        history_before = await get_thread(
            db, conversation_id=conversation.id, leaf_message_id=user_message.parent_message_id
        )
        history_text = conversation_history_text(history_before)
        return await _generate_assistant_reply(
            db,
            user=user,
            conversation=conversation,
            user_message=user_message,
            history_before_text=history_text,
        )

    return await _with_assistant_quota(db, user=user, generate=_generate)


async def edit_and_branch(
    db: AsyncSession,
    *,
    user: User,
    conversation: Conversation,
    message_id: uuid.UUID,
    new_text: str,
) -> TurnResult:
    """Editing a user message never destroys history: it creates a new
    sibling user message under the same parent, then generates a fresh
    assistant reply following it -- the original branch is still there
    for `get_thread(leaf_message_id=...)` to return."""

    async def _generate() -> Message:
        original = await get_owned_message(
            db, user_id=user.id, conversation_id=conversation.id, message_id=message_id
        )
        if original.role != "user":
            raise ApiError(ErrorCode.VALIDATION_FAILED, "only a user message can be edited")
        new_user_message = await append_message(
            db,
            conversation=conversation,
            role="user",
            content=new_text,
            parent_message_id=original.parent_message_id,
        )
        history_before = await get_thread(
            db, conversation_id=conversation.id, leaf_message_id=original.parent_message_id
        )
        history_text = conversation_history_text(history_before)
        return await _generate_assistant_reply(
            db,
            user=user,
            conversation=conversation,
            user_message=new_user_message,
            history_before_text=history_text,
        )

    return await _with_assistant_quota(db, user=user, generate=_generate)


async def confirm_and_run_tool(
    db: AsyncSession,
    *,
    user: User,
    conversation: Conversation,
    proposing_message_id: uuid.UUID,
    tool_id: str,
    input_data: dict[str, Any],
) -> Message:
    """Runs the exact tool the user confirmed from a proposal card, via
    the same `app.tools.service.run_tool` every hub page calls -- nothing
    here re-implements tool execution. Records the result as a
    `role="tool"` message linked to both the proposing assistant message
    and the real `ToolRun`, so "what happened" is visible in the
    transcript and traceable back to `tool_runs`/`ai_invocations` exactly
    like a hub-run tool."""
    run, _quota, _warning = await tools_service.run_tool(
        db, user=user, tool_id=tool_id, raw_input=input_data
    )
    return await append_message(
        db,
        conversation=conversation,
        role="tool",
        content=f"Ran {tool_id} (run {run.id}, status: {run.status}).",
        tool_call={"tool_id": tool_id, "run_id": str(run.id), "status": run.status},
        tool_run_id=run.id,
        parent_message_id=proposing_message_id,
    )


async def stream_message(
    db: AsyncSession, *, user: User, conversation: Conversation, text: str
) -> AsyncIterator[dict[str, Any]]:
    """The streaming counterpart to `handle_message`: a visible `start`
    frame goes out immediately, intent classification and any canned
    response (policy refusal, out-of-scope redirect, coach hand-off,
    coach mode itself) resolve in one frame the same as the non-streaming
    path, and only the reply-generation call for `smalltalk`/`explain`/
    `run_tool`/`analyse_my_data` actually streams token deltas from the
    gateway -- mirroring app.tools.service's own `_stream_and_persist`
    (validation before persistence, an `error` frame instead of a raised
    exception once headers are already on the wire). A dropped client
    connection simply stops this generator being iterated; there is
    nothing further to clean up since every write here already commits
    as it goes, exactly like the non-streaming path."""
    try:
        reservation = await check_and_reserve(db, user=user, metric=ASSISTANT_MESSAGES_METRIC)
    except ApiError as exc:
        yield {"type": "error", "code": exc.code.value, "message": exc.message}
        return

    yield {"type": "start"}

    async def _final(message: Message) -> dict[str, Any]:
        quota = await peek(db, user=user, metric=ASSISTANT_MESSAGES_METRIC)
        return {
            "type": "message",
            "message": to_message_response(message).model_dump(mode="json"),
            "quota": to_quota_info(quota).model_dump(mode="json"),
            "quota_warning": _quota_warning(quota),
        }

    try:
        if conversation.mode == "coach":
            from app.growth import coach as growth_coach

            message = await growth_coach.send_message(
                db, user=user, conversation=conversation, text=text
            )
            yield await _final(message)
            return

        if conversation.mode not in ("auto", "tool"):
            raise UnknownConversationMode(conversation.mode)

        thread = await get_thread(db, conversation_id=conversation.id)
        prior_leaf_id = thread[-1].id if thread else None
        history_text = conversation_history_text(thread)
        user_message = await append_message(
            db,
            conversation=conversation,
            role="user",
            content=text,
            parent_message_id=prior_leaf_id,
        )

        refusal = policy.check_input(text)
        if refusal is not None:
            message = await append_message(
                db,
                conversation=conversation,
                role="assistant",
                content=refusal.message,
                parent_message_id=user_message.id,
                tool_call={"intent": "policy_violation", "policy_category": refusal.category},
            )
            yield await _final(message)
            return

        pinned_tool_id = _pinned_tool_id(conversation) if conversation.mode == "tool" else None
        if pinned_tool_id is not None:
            intent, tool_candidates, needs_context = "run_tool", [pinned_tool_id], []
            policy_category = None
        else:
            classification = await _classify_intent(
                db, user=user, history_text=history_text, text=text
            )
            intent = classification["intent"]
            tool_candidates = list(classification.get("tool_candidates") or [])
            needs_context = list(classification.get("needs_context") or [])
            policy_category = classification.get("policy_category")

        canned_by_intent = {
            "policy_violation": policy.refusal_message_for_category(
                policy_category, fallback=_GENERIC_POLICY_REFUSAL
            ),
            "out_of_scope": _OUT_OF_SCOPE_REPLY,
            "coach": _COACH_REDIRECT_REPLY,
        }
        if intent in canned_by_intent:
            message = await append_message(
                db,
                conversation=conversation,
                role="assistant",
                content=canned_by_intent[intent],
                parent_message_id=user_message.id,
                tool_call={"intent": intent, "policy_category": policy_category},
            )
            yield await _final(message)
            return

        context, tier = await _build_reply_context(
            db,
            user=user,
            conversation=conversation,
            user_message=user_message,
            history_text=history_text,
            text=text,
            intent=intent,
            tool_candidates=tool_candidates,
            needs_context=needs_context,
        )

        text_parts: list[str] = []
        tokens_out = 0
        correlation_id: str | None = None
        async for frame in gateway.run(
            "assistant.reply.v1", context, user=user, db=db, tier_override=tier, stream=True
        ):
            if frame["type"] == "delta":
                text_parts.append(frame["text"])
                yield {"type": "delta", "text": frame["text"]}
            elif frame["type"] == "meta":
                correlation_id = frame.get("correlation_id")
            elif frame["type"] == "error":
                await release(db, reservation)
                yield frame
                return
            elif frame["type"] == "done":
                tokens_out = frame.get("tokens_out", 0)

        full_text = "".join(text_parts)
        try:
            parsed = json.loads(full_text)
        except json.JSONDecodeError:
            parsed = {"reply": full_text, "proposed_tool": None}
        reply_text, proposed_tool = await _finalize_reply(
            db,
            parsed,
            user_id=user.id,
            conversation_id=conversation.id,
            tool_candidates=tool_candidates,
        )

        invocation_id = None
        if correlation_id is not None:
            invocation = (
                await db.execute(
                    select(AIInvocation).where(AIInvocation.correlation_id == correlation_id)
                )
            ).scalar_one_or_none()
            if invocation is not None:
                invocation_id = invocation.id

        message = await append_message(
            db,
            conversation=conversation,
            role="assistant",
            content=reply_text,
            ai_invocation_id=invocation_id,
            parent_message_id=user_message.id,
            tool_call={"intent": intent, "proposed_tool": proposed_tool},
            tokens=tokens_out,
        )
        yield await _final(message)
    except Exception:
        await release(db, reservation)
        raise


async def rate_message(
    db: AsyncSession, *, user: User, conversation_id: uuid.UUID, message_id: uuid.UUID, rating: str
) -> Message:
    message = await get_owned_message(
        db, user_id=user.id, conversation_id=conversation_id, message_id=message_id
    )
    message.tool_call = {**(message.tool_call or {}), "rating": rating}
    await db.commit()
    await db.refresh(message)
    return message
