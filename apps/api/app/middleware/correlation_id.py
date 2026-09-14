"""Assigns a per-request id (reusing an inbound `X-Request-ID` if a proxy
or the caller already set one, generating a fresh one otherwise), makes
it available to every log line emitted while handling the request via
app/observability/logging.py's contextvar, and echoes it back as a
response header so a client or proxy log can be correlated with ours."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.logging import (
    REQUEST_ID_HEADER,
    new_request_id,
    reset_request_id,
    set_request_id,
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            # Without this, the id leaks into whatever context called us --
            # harmless across real requests (each gets a fresh ASGI task
            # with its own context), but very much observable in-process,
            # e.g. an httpx ASGITransport test client sharing the test's
            # own async context with the app it's calling.
            reset_request_id(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
