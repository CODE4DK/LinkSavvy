from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, field_validator

if TYPE_CHECKING:
    from app.models.user import User


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

    @classmethod
    def from_model(cls, user: User) -> UserPublic:
        return cls(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            locale=user.locale,
            timezone=user.timezone,
            role=user.role,
            plan=user.plan,
            email_verified=user.email_verified_at is not None,
            created_at=user.created_at,
        )


class MeResponse(BaseModel):
    user: UserPublic
    feature_flags: dict[str, bool]


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    locale: str | None = None
    timezone: str | None = None

    @field_validator("full_name")
    @classmethod
    def _full_name_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Full name cannot be blank")
        return value.strip() if value is not None else value

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {value}") from exc
        return value
