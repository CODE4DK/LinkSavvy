"""Double-submit CSRF protection for the two endpoints that authenticate
purely from a cookie with no bearer token at all: `POST /auth/refresh`
and `POST /auth/logout`. Every other mutating endpoint requires a bearer
access token in an `Authorization` header, which a cross-site form or
script can't attach -- there's nothing for CSRF to exploit there. The
refresh cookie's own `SameSite=Lax` already blocks it being sent on a
cross-site POST in a compliant browser; this is the defense-in-depth
layer for browsers or configurations where that alone isn't a given.
"""

from __future__ import annotations

import hmac
import secrets

from fastapi import Request

from app.errors import ApiError, ErrorCode

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def verify_csrf(request: Request) -> None:
    """Only enforced once a CSRF cookie actually exists -- that cookie is
    set exactly when a refresh-token cookie is (see
    app/routers/auth.py::_set_refresh_cookie), so its absence means there
    is no cookie-based session for a forged request to ride on in the
    first place. That case is left to the endpoint's own "no refresh
    token presented" handling, which gives a clearer error than a generic
    CSRF failure would."""
    cookie_value = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie_value:
        return
    header_value = request.headers.get(CSRF_HEADER_NAME)
    if not header_value or not hmac.compare_digest(cookie_value, header_value):
        raise ApiError(ErrorCode.FORBIDDEN, "Missing or invalid CSRF token")
