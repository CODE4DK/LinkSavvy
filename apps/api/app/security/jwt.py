"""Short-lived access JWTs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import PyJWTError

from app.settings import settings

ALGORITHM = "HS256"


class AccessTokenError(Exception):
    pass


def create_access_token(user_id: uuid.UUID, *, role: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except PyJWTError as exc:
        raise AccessTokenError(str(exc)) from exc
    if payload.get("type") != "access":
        raise AccessTokenError("wrong token type")
    return payload
