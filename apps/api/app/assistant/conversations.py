"""The one conversation store every assistant surface writes into --
the general Assistant (`mode="auto"`/`"tool"`) and the absorbed Growth
Coach (`mode="coach"`, see app/growth/coach.py) alike. Nothing here
knows about intents, tools, or coaching prompts; it's the same
create/list/append/branch/archive/delete primitives regardless of mode.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

_TITLE_MAX_LENGTH = 60


class ConversationNotFound(ApiError):
    def __init__(self) -> None:
        super().__init__(ErrorCode.NOT_FOUND, "no such conversation")


def _auto_title(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _TITLE_MAX_LENGTH:
        return collapsed
    return collapsed[:_TITLE_MAX_LENGTH].rstrip() + "…"


async def get_owned_conversation(
    db: AsyncSession, *, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation:
    conversation = await db.get(Conversation, conversation_id)
    if (
        conversation is None
        or conversation.user_id != user_id
        or conversation.deleted_at is not None
    ):
        raise ConversationNotFound()
    return conversation


async def get_or_create_active_conversation(
    db: AsyncSession, *, user: User, mode: str
) -> Conversation:
    """The conversation a given mode resumes by default: its most
    recently active (non-archived, non-deleted) thread, or a fresh one.
    Used for the absorbed Growth Coach (always one ongoing `coach`
    conversation) and can be reused by any other single-thread surface;
    the general Assistant's own conversation list instead lets the user
    pick or start one explicitly via `create_conversation`."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.user_id == user.id,
            Conversation.mode == mode,
            Conversation.is_archived.is_(False),
            Conversation.deleted_at.is_(None),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        return conversation
    return await create_conversation(db, user=user, mode=mode)


async def create_conversation(
    db: AsyncSession,
    *,
    user: User,
    mode: str = "auto",
    context_snapshot: dict[str, Any] | None = None,
) -> Conversation:
    conversation = Conversation(user_id=user.id, mode=mode, context_snapshot=context_snapshot)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def list_conversations(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    q: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
) -> list[Conversation]:
    stmt = select(Conversation).where(
        Conversation.user_id == user_id, Conversation.deleted_at.is_(None)
    )
    if not include_archived:
        stmt = stmt.where(Conversation.is_archived.is_(False))
    if q:
        stmt = stmt.where(Conversation.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def rename_conversation(
    db: AsyncSession, *, user_id: uuid.UUID, conversation_id: uuid.UUID, title: str
) -> Conversation:
    conversation = await get_owned_conversation(
        db, user_id=user_id, conversation_id=conversation_id
    )
    conversation.title = title.strip() or None
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def set_archived(
    db: AsyncSession, *, user_id: uuid.UUID, conversation_id: uuid.UUID, archived: bool
) -> Conversation:
    conversation = await get_owned_conversation(
        db, user_id=user_id, conversation_id=conversation_id
    )
    conversation.is_archived = archived
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def delete_conversation(
    db: AsyncSession, *, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> None:
    conversation = await get_owned_conversation(
        db, user_id=user_id, conversation_id=conversation_id
    )
    conversation.deleted_at = datetime.now(UTC)
    await db.commit()


async def list_messages(db: AsyncSession, *, conversation_id: uuid.UUID) -> list[Message]:
    """The flat, all-branches history for a conversation, oldest first --
    the raw material `get_thread` walks to find one linear path, and what
    a branch-switcher UI needs to know which messages are siblings."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def get_thread(
    db: AsyncSession, *, conversation_id: uuid.UUID, leaf_message_id: uuid.UUID | None = None
) -> list[Message]:
    """One linear path through the conversation's message tree, root
    first -- what actually renders as "the conversation". Editing a
    message branches (see `edit_and_branch`) rather than destroying
    history, so without a pinned `leaf_message_id` this defaults to the
    path ending at the most recently created leaf (a message nothing
    else lists as its parent) -- i.e. the newest branch. Passing an
    older message's id as `leaf_message_id` is how the UI's "switch
    branch" control asks for a different path instead."""
    all_messages = await list_messages(db, conversation_id=conversation_id)
    if not all_messages:
        return []
    by_id = {message.id: message for message in all_messages}

    leaf: Message | None
    if leaf_message_id is not None:
        leaf = by_id.get(leaf_message_id)
        if leaf is None:
            return []
    else:
        parents = {
            message.parent_message_id for message in all_messages if message.parent_message_id
        }
        leaves = [message for message in all_messages if message.id not in parents]
        leaf = max(leaves, key=lambda m: m.created_at) if leaves else all_messages[-1]

    path: list[Message] = []
    current: Message | None = leaf
    while current is not None:
        path.append(current)
        current = by_id.get(current.parent_message_id) if current.parent_message_id else None
    path.reverse()
    return path


async def append_message(
    db: AsyncSession,
    *,
    conversation: Conversation,
    role: str,
    content: str,
    tool_call: dict[str, Any] | None = None,
    tool_run_id: uuid.UUID | None = None,
    ai_invocation_id: uuid.UUID | None = None,
    parent_message_id: uuid.UUID | None = None,
    tokens: int | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        tool_call=tool_call,
        tool_run_id=tool_run_id,
        ai_invocation_id=ai_invocation_id,
        parent_message_id=parent_message_id,
        tokens=tokens,
    )
    db.add(message)
    conversation.message_count += 1
    conversation.last_message_at = datetime.now(UTC)
    if conversation.title is None and role == "user":
        conversation.title = _auto_title(content)
    await db.commit()
    await db.refresh(message)
    return message


async def get_owned_message(
    db: AsyncSession, *, user_id: uuid.UUID, conversation_id: uuid.UUID, message_id: uuid.UUID
) -> Message:
    await get_owned_conversation(db, user_id=user_id, conversation_id=conversation_id)
    message = await db.get(Message, message_id)
    if message is None or message.conversation_id != conversation_id:
        raise ApiError(ErrorCode.NOT_FOUND, "no such message")
    return message
