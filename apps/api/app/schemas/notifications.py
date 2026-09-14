from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

ChannelLiteral = Literal["in_app", "email"]


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str
    action_route: str | None
    metadata: dict[str, Any]
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int


class PreferenceRow(BaseModel):
    channel: ChannelLiteral
    type: str
    enabled: bool


class PreferencesResponse(BaseModel):
    preferences: list[PreferenceRow]


class SetPreferenceRequest(BaseModel):
    channel: ChannelLiteral
    type: str
    enabled: bool
