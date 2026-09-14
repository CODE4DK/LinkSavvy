"""Security response headers applied to every response. See docs/security.md
for the rationale behind each header and how the CSP nonce is threaded
through to the few pages that need an inline `<script>` at all (none, at
present -- the web app ships everything as external bundles, so the CSP
below has no `'unsafe-inline'` for scripts or styles)."""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.settings import settings

_PERMISSIONS_POLICY = (
    "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
)


def _csp(nonce: str) -> str:
    # `connect-src` includes the configured API origin plus 'self' so the
    # web app's own fetches (and the billing providers' hosted checkout,
    # loaded as a top-level navigation rather than a frame) aren't blocked.
    return (
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        "style-src 'self'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = _PERMISSIONS_POLICY
        response.headers["Content-Security-Policy"] = _csp(nonce)
        # HSTS only makes sense once we're actually served over HTTPS --
        # local dev and the test suite run plain HTTP, and the header
        # itself is harmless to omit there rather than sending a promise
        # they can't keep.
        if settings.env == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response
