from __future__ import annotations

import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.errors import ApiError, ErrorCode
from app.models.user import User
from app.security.jwt import AccessTokenError, decode_access_token

__all__ = ["get_db", "get_current_user", "client_ip"]


def _extract_bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, "Missing bearer token")
    return header.split(" ", 1)[1]


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = _extract_bearer_token(request)
    try:
        payload = decode_access_token(token)
    except AccessTokenError as exc:
        raise ApiError(ErrorCode.TOKEN_EXPIRED, "Access token is invalid or expired") from exc

    user_id = uuid.UUID(payload["sub"])
    user = await db.get(User, user_id)
    if user is None or user.status != "active" or user.deleted_at is not None:
        raise ApiError(ErrorCode.FORBIDDEN, "Account is not active")
    return user


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
