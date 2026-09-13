"""The AI Assistant's public API: conversations, messages, tool
confirmation, context toggles, and suggested prompts. A thin HTTP layer
over app/assistant/{orchestrator,conversations,suggestions}.py -- see
docs/adr/0010.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant import conversations as conversations_service
from app.assistant import orchestrator
from app.assistant.orchestrator import ALL_CONTEXT_KEYS, excluded_context_keys
from app.assistant.presenters import to_conversation_summary, to_message_response, to_quota_info
from app.assistant.suggestions import suggested_prompts
from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.asset import Asset
from app.models.user import User
from app.schemas.assistant import (
    ArchiveConversationRequest,
    ConfirmToolRunRequest,
    ContextItemResponse,
    ContextSettingsResponse,
    ContextTogglesRequest,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationSummary,
    EditMessageRequest,
    MessageResponse,
    RateMessageRequest,
    RenameConversationRequest,
    SaveConversationRequest,
    SendMessageRequest,
    SendMessageResponse,
    SuggestedPromptsResponse,
)
from app.tools.context import ContextKey

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])

_CONTEXT_KEY_LABELS: dict[ContextKey, str] = {
    ContextKey.PROFILE_IDENTITY: "Your identity (name, industry, location)",
    ContextKey.PROFILE_HEADLINE: "Your current headline",
    ContextKey.AUDIT_SUMMARY: "Your latest audit summary",
    ContextKey.GROWTH_GOAL: "Your active growth goal",
    ContextKey.RECENT_ASSET_TITLES: "Titles of your 10 most recent saved items",
}


@router.get("/suggested-prompts", response_model=SuggestedPromptsResponse)
async def get_suggested_prompts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuggestedPromptsResponse:
    return SuggestedPromptsResponse(prompts=await suggested_prompts(db, user=user))


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations_endpoint(
    q: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationSummary]:
    conversations = await conversations_service.list_conversations(
        db, user_id=user.id, q=q, include_archived=include_archived
    )
    return [to_conversation_summary(c) for c in conversations]


@router.post("/conversations", response_model=ConversationSummary)
async def create_conversation_endpoint(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummary:
    context_snapshot: dict[str, Any] | None = None
    if payload.mode == "tool":
        if payload.tool_id is None:
            raise ApiError(ErrorCode.VALIDATION_FAILED, "mode 'tool' requires a tool_id")
        context_snapshot = {"pinned_tool_id": payload.tool_id}
    conversation = await conversations_service.create_conversation(
        db, user=user, mode=payload.mode, context_snapshot=context_snapshot
    )
    return to_conversation_summary(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_endpoint(
    conversation_id: uuid.UUID,
    leaf_message_id: uuid.UUID | None = Query(default=None),
    all_branches: bool = Query(
        default=False, description="Return every branch, not just the active thread"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailResponse:
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    messages = (
        await conversations_service.list_messages(db, conversation_id=conversation.id)
        if all_branches
        else await conversations_service.get_thread(
            db, conversation_id=conversation.id, leaf_message_id=leaf_message_id
        )
    )
    return ConversationDetailResponse(
        conversation=to_conversation_summary(conversation),
        messages=[to_message_response(m) for m in messages],
    )


@router.post("/conversations/{conversation_id}/rename", response_model=ConversationSummary)
async def rename_conversation_endpoint(
    conversation_id: uuid.UUID,
    payload: RenameConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummary:
    conversation = await conversations_service.rename_conversation(
        db, user_id=user.id, conversation_id=conversation_id, title=payload.title
    )
    return to_conversation_summary(conversation)


@router.post("/conversations/{conversation_id}/archive", response_model=ConversationSummary)
async def archive_conversation_endpoint(
    conversation_id: uuid.UUID,
    payload: ArchiveConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummary:
    conversation = await conversations_service.set_archived(
        db, user_id=user.id, conversation_id=conversation_id, archived=payload.archived
    )
    return to_conversation_summary(conversation)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation_endpoint(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await conversations_service.delete_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )


@router.post("/conversations/{conversation_id}/save", response_model=ConversationSummary)
async def save_conversation_endpoint(
    conversation_id: uuid.UUID,
    payload: SaveConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummary:
    """Saves this conversation into Workspace as a `conversation` asset
    (the asset type Phase 05 already defined) -- a transcript of the
    active thread, not a live link, so it stays intact even if the
    conversation itself is later edited or deleted."""
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    thread = await conversations_service.get_thread(db, conversation_id=conversation.id)
    transcript = "\n\n".join(f"{m.role.upper()}: {m.content}" for m in thread)
    title = payload.title or conversation.title or "Assistant conversation"
    asset = Asset(
        user_id=user.id, type="conversation", title=title, body=transcript, body_format="text"
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    conversation.asset_id = asset.id
    await db.commit()
    await db.refresh(conversation)
    return to_conversation_summary(conversation)


@router.get("/conversations/{conversation_id}/context", response_model=ContextSettingsResponse)
async def get_context_settings_endpoint(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContextSettingsResponse:
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    excluded = excluded_context_keys(conversation)
    return ContextSettingsResponse(
        items=[
            ContextItemResponse(
                key=key.value, label=_CONTEXT_KEY_LABELS[key], excluded=key.value in excluded
            )
            for key in ALL_CONTEXT_KEYS
        ]
    )


@router.patch("/conversations/{conversation_id}/context", response_model=ContextSettingsResponse)
async def update_context_settings_endpoint(
    conversation_id: uuid.UUID,
    payload: ContextTogglesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContextSettingsResponse:
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    snapshot = dict(conversation.context_snapshot or {})
    snapshot["excluded_context_keys"] = payload.excluded_context_keys
    conversation.context_snapshot = snapshot
    await db.commit()
    return await get_context_settings_endpoint(conversation_id, user=user, db=db)


async def _sse_events(frames: AsyncIterator[dict[str, Any]]) -> AsyncIterator[str]:
    async for frame in frames:
        yield f"data: {json.dumps(frame)}\n\n"


@router.post("/conversations/{conversation_id}/messages", response_model=None)
async def send_message_endpoint(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    stream: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse | StreamingResponse:
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    if stream:
        frames = orchestrator.stream_message(
            db, user=user, conversation=conversation, text=payload.text
        )
        return StreamingResponse(_sse_events(frames), media_type="text/event-stream")

    result = await orchestrator.handle_message(
        db, user=user, conversation=conversation, text=payload.text
    )
    return SendMessageResponse(
        message=to_message_response(result.message),
        quota=to_quota_info(result.quota),
        quota_warning=result.quota_warning,
    )


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/retry",
    response_model=SendMessageResponse,
)
async def retry_message_endpoint(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    result = await orchestrator.retry_message(
        db, user=user, conversation=conversation, user_message_id=message_id
    )
    return SendMessageResponse(
        message=to_message_response(result.message),
        quota=to_quota_info(result.quota),
        quota_warning=result.quota_warning,
    )


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/edit",
    response_model=SendMessageResponse,
)
async def edit_message_endpoint(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: EditMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    result = await orchestrator.edit_and_branch(
        db, user=user, conversation=conversation, message_id=message_id, new_text=payload.text
    )
    return SendMessageResponse(
        message=to_message_response(result.message),
        quota=to_quota_info(result.quota),
        quota_warning=result.quota_warning,
    )


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/rate", response_model=MessageResponse
)
async def rate_message_endpoint(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: RateMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    message = await orchestrator.rate_message(
        db,
        user=user,
        conversation_id=conversation_id,
        message_id=message_id,
        rating=payload.rating,
    )
    return to_message_response(message)


@router.post("/conversations/{conversation_id}/confirm-tool", response_model=MessageResponse)
async def confirm_tool_endpoint(
    conversation_id: uuid.UUID,
    payload: ConfirmToolRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    conversation = await conversations_service.get_owned_conversation(
        db, user_id=user.id, conversation_id=conversation_id
    )
    message = await orchestrator.confirm_and_run_tool(
        db,
        user=user,
        conversation=conversation,
        proposing_message_id=payload.message_id,
        tool_id=payload.tool_id,
        input_data=payload.input,
    )
    return to_message_response(message)
