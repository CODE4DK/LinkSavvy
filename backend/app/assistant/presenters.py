"""ORM -> response-schema conversion for the Assistant router, plus the
same shaping for a streamed SSE frame's `message` field (`.model_dump
(mode="json")` on the same `AssistantMessageResponse` covers both -- one
conversion path, not two)."""

from __future__ import annotations

from app.billing.quota import QuotaStatus
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.assistant import AssistantMessageResponse, ConversationSummary
from app.schemas.tools import QuotaInfo


def to_conversation_summary(conversation: Conversation) -> ConversationSummary:
    return ConversationSummary(
        id=str(conversation.id),
        title=conversation.title,
        mode=conversation.mode,
        message_count=conversation.message_count,
        last_message_at=conversation.last_message_at,
        is_archived=conversation.is_archived,
        asset_id=str(conversation.asset_id) if conversation.asset_id else None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def to_message_response(message: Message) -> AssistantMessageResponse:
    return AssistantMessageResponse(
        id=str(message.id),
        role=message.role,
        content=message.content,
        tool_call=message.tool_call,
        tool_run_id=str(message.tool_run_id) if message.tool_run_id else None,
        parent_message_id=str(message.parent_message_id) if message.parent_message_id else None,
        created_at=message.created_at,
    )


def to_quota_info(quota: QuotaStatus) -> QuotaInfo:
    return QuotaInfo(metric=quota.metric, used=quota.used, limit=quota.limit)
