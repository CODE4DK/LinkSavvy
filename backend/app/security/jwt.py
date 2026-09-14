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


# Admin impersonation (Phase 10). A separate token type -- never "access"
# -- so a stolen impersonation token can never be mistaken for the
# admin's own session, and so app/middleware/impersonation_guard.py can
# recognise and block it on any unsafe HTTP method without get_current_user
# needing to know anything about impersonation at all.
IMPERSONATION_TOKEN_TYPE = "impersonation"
DEFAULT_IMPERSONATION_TTL_MINUTES = 30


def create_impersonation_token(
    *,
    admin_id: uuid.UUID,
    target_user_id: uuid.UUID,
    target_role: str,
    ttl_minutes: int = DEFAULT_IMPERSONATION_TTL_MINUTES,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(target_user_id),
        "role": target_role,
        "impersonator_id": str(admin_id),
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
        "type": IMPERSONATION_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_user_token(token: str) -> dict[str, Any]:
    """Accepts either an ordinary access token or an impersonation token
    -- used by get_current_user, which doesn't care which one it got, only
    that it names a real user. Callers that must tell the two apart (the
    impersonation guard) check `payload["type"]` themselves."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except PyJWTError as exc:
        raise AccessTokenError(str(exc)) from exc
    if payload.get("type") not in ("access", IMPERSONATION_TOKEN_TYPE):
        raise AccessTokenError("wrong token type")
    return payload
