from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    avatar_url: str | None
    locale: str
    timezone: str
    role: str
    plan: str
    email_verified: bool
    created_at: datetime


class MeResponse(BaseModel):
    user: UserPublic
    feature_flags: dict[str, bool]
