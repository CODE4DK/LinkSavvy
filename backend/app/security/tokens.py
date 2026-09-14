"""Opaque single-use tokens (email verification, password reset, refresh).

The raw token is handed to the user (in a URL or a cookie); only its
salted hash is ever persisted, so a leaked database dump cannot be
replayed as a live session or verification link.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from app.settings import settings


def generate_raw_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str, *, pepper: str | None = None) -> str:
    key = (pepper or settings.refresh_token_pepper).encode("utf-8")
    return hmac.new(key, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    key = settings.refresh_token_pepper.encode("utf-8")
    return hmac.new(key, ip.encode("utf-8"), hashlib.sha256).hexdigest()
