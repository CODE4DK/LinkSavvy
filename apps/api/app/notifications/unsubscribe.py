"""One-click unsubscribe tokens. Deliberately not a JWT -- there's
nothing here that needs expiry or claims beyond "which user, which
notification type", and a link that a mail client can GET with no auth
header needs to carry its own proof rather than relying on a session.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import uuid

from app.settings import settings


class InvalidUnsubscribeToken(Exception):
    pass


def _sign(payload: str) -> str:
    digest = hmac.new(settings.unsubscribe_secret.encode(), payload.encode(), hashlib.sha256)
    return base64.urlsafe_b64encode(digest.digest()).decode().rstrip("=")


def make_unsubscribe_token(*, user_id: uuid.UUID, notification_type: str) -> str:
    payload = f"{user_id}:{notification_type}"
    signature = _sign(payload)
    raw = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def parse_unsubscribe_token(token: str) -> tuple[uuid.UUID, str]:
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode()).decode()
        user_id_str, notification_type, signature = raw.rsplit(":", 2)
    except (ValueError, UnicodeDecodeError) as exc:
        raise InvalidUnsubscribeToken("malformed token") from exc

    expected = _sign(f"{user_id_str}:{notification_type}")
    if not hmac.compare_digest(expected, signature):
        raise InvalidUnsubscribeToken("signature mismatch")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise InvalidUnsubscribeToken("malformed user id") from exc

    return user_id, notification_type


def unsubscribe_url(*, user_id: uuid.UUID, notification_type: str) -> str:
    """Points at the API directly (not the SPA) -- RFC 8058's one-click
    unsubscribe means a mail client POSTs this URL itself, with no
    frontend involved to relay the request."""
    token = make_unsubscribe_token(user_id=user_id, notification_type=notification_type)
    return f"{settings.api_public_url}/api/v1/notifications/unsubscribe?token={token}"
