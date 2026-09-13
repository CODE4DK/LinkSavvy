from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant import conversations as service
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"assistant-{uuid.uuid4()}@example.com", full_name="Assistant Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_create_and_get_owned_conversation(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    conversation = await service.create_conversation(db_session, user=user, mode="auto")
    fetched = await service.get_owned_conversation(
        db_session, user_id=user.id, conversation_id=conversation.id
    )
    assert fetched.id == conversation.id
    assert fetched.mode == "auto"
    assert fetched.title is None


async def test_get_owned_conversation_rejects_another_users_conversation(
    db_session: AsyncSession,
) -> None:
    owner = await _create_user(db_session)
    other = await _create_user(db_session)
    conversation = await service.create_conversation(db_session, user=owner, mode="auto")
    try:
        await service.get_owned_conversation(
            db_session, user_id=other.id, conversation_id=conversation.id
        )
        raise AssertionError("expected ConversationNotFound")
    except service.ConversationNotFound:
        pass


async def test_get_or_create_active_conversation_is_idempotent_per_mode(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    first = await service.get_or_create_active_conversation(db_session, user=user, mode="coach")
    second = await service.get_or_create_active_conversation(db_session, user=user, mode="coach")
    assert first.id == second.id

    other_mode = await service.get_or_create_active_conversation(db_session, user=user, mode="auto")
    assert other_mode.id != first.id


async def test_get_or_create_active_conversation_skips_archived(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    first = await service.get_or_create_active_conversation(db_session, user=user, mode="coach")
    await service.set_archived(db_session, user_id=user.id, conversation_id=first.id, archived=True)
    second = await service.get_or_create_active_conversation(db_session, user=user, mode="coach")
    assert second.id != first.id


async def test_append_message_sets_title_from_first_user_message_and_bumps_count(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    conversation = await service.create_conversation(db_session, user=user)

    await service.append_message(
        db_session, conversation=conversation, role="user", content="Fix my headline please"
    )
    assert conversation.title == "Fix my headline please"
    assert conversation.message_count == 1

    await service.append_message(
        db_session, conversation=conversation, role="assistant", content="Sure, here's a draft."
    )
    assert conversation.title == "Fix my headline please"  # unchanged by later messages
    assert conversation.message_count == 2


async def test_append_message_truncates_a_long_title() -> None:
    long_text = "x" * 200
    title = service._auto_title(long_text)  # noqa: SLF001
    assert len(title) <= 61  # 60 chars + the ellipsis character
    assert title.endswith("…")


async def test_list_conversations_filters_by_search_query(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    a = await service.create_conversation(db_session, user=user)
    b = await service.create_conversation(db_session, user=user)
    await service.append_message(db_session, conversation=a, role="user", content="Resume advice")
    await service.append_message(db_session, conversation=b, role="user", content="Headline help")

    results = await service.list_conversations(db_session, user_id=user.id, q="resume")
    assert [c.id for c in results] == [a.id]


async def test_get_thread_defaults_to_the_newest_leaf(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    conversation = await service.create_conversation(db_session, user=user)

    m1 = await service.append_message(
        db_session, conversation=conversation, role="user", content="Hi"
    )
    m2 = await service.append_message(
        db_session,
        conversation=conversation,
        role="assistant",
        content="Hello!",
        parent_message_id=m1.id,
    )
    m3 = await service.append_message(
        db_session,
        conversation=conversation,
        role="user",
        content="Help with X",
        parent_message_id=m2.id,
    )

    thread = await service.get_thread(db_session, conversation_id=conversation.id)
    assert [m.id for m in thread] == [m1.id, m2.id, m3.id]


async def test_get_thread_follows_a_branch_when_leaf_message_id_is_given(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    conversation = await service.create_conversation(db_session, user=user)

    root = await service.append_message(
        db_session, conversation=conversation, role="user", content="Hi"
    )
    original_reply = await service.append_message(
        db_session,
        conversation=conversation,
        role="assistant",
        content="First answer",
        parent_message_id=root.id,
    )
    # A branch: a sibling reply under the same parent (as if the user's
    # message were retried), created *after* original_reply.
    branch_reply = await service.append_message(
        db_session,
        conversation=conversation,
        role="assistant",
        content="Second answer",
        parent_message_id=root.id,
    )

    default_thread = await service.get_thread(db_session, conversation_id=conversation.id)
    assert [m.id for m in default_thread] == [root.id, branch_reply.id]

    old_branch_thread = await service.get_thread(
        db_session, conversation_id=conversation.id, leaf_message_id=original_reply.id
    )
    assert [m.id for m in old_branch_thread] == [root.id, original_reply.id]


async def test_editing_a_message_creates_a_sibling_not_a_child(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    conversation = await service.create_conversation(db_session, user=user)

    root = await service.append_message(
        db_session, conversation=conversation, role="user", content="Hi"
    )
    reply = await service.append_message(
        db_session,
        conversation=conversation,
        role="assistant",
        content="Answer",
        parent_message_id=root.id,
    )
    edited_root = await service.append_message(
        db_session,
        conversation=conversation,
        role="user",
        content="Hi, edited",
        parent_message_id=root.parent_message_id,
    )

    assert edited_root.parent_message_id == root.parent_message_id
    assert edited_root.id != root.id

    all_messages = await service.list_messages(db_session, conversation_id=conversation.id)
    assert {m.id for m in all_messages} == {root.id, reply.id, edited_root.id}


async def test_delete_conversation_soft_deletes(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    conversation = await service.create_conversation(db_session, user=user)
    await service.delete_conversation(db_session, user_id=user.id, conversation_id=conversation.id)

    try:
        await service.get_owned_conversation(
            db_session, user_id=user.id, conversation_id=conversation.id
        )
        raise AssertionError("expected ConversationNotFound")
    except service.ConversationNotFound:
        pass
