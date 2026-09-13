from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.tools import QuotaInfo

_TEXT_MAX_LENGTH = 8000


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["auto", "tool"] = "auto"
    tool_id: str | None = None


class ConversationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str | None
    mode: str
    message_count: int
    last_message_at: datetime | None
    is_archived: bool
    asset_id: str | None
    created_at: datetime
    updated_at: datetime


class ProposedToolResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_id: str
    reasoning: str
    prefilled_input: dict[str, Any]


class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    role: str
    content: str
    tool_call: dict[str, Any] | None
    tool_run_id: str | None
    parent_message_id: str | None
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation: ConversationSummary
    messages: list[MessageResponse]


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=_TEXT_MAX_LENGTH)


class SendMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: MessageResponse
    quota: QuotaInfo
    quota_warning: str | None = None


class EditMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=_TEXT_MAX_LENGTH)


class RenameConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str


class ArchiveConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archived: bool


class ConfirmToolRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: uuid.UUID
    tool_id: str
    input: dict[str, Any]


class RateMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: Literal["up", "down"]


class ContextItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    excluded: bool


class ContextSettingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ContextItemResponse]


class ContextTogglesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    excluded_context_keys: list[str]


class SaveConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None


class SuggestedPromptsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompts: list[str]
