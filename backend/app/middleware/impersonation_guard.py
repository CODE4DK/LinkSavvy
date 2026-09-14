"""Enforces "impersonation is read-only" at the transport level, not by
trusting every route handler to remember to check.

An admin's impersonation token (see app/security/jwt.py::
create_impersonation_token) is a different `type` claim than an ordinary
access token specifically so this middleware can recognise it without
decoding it twice or teaching every dependency about impersonation. It
runs before routing, so a blocked request never reaches a handler, a
quota check, or a job enqueue -- there is no path through the app that
lets an impersonation token perform a write.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import jwt as pyjwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.security.jwt import ALGORITHM, IMPERSONATION_TOKEN_TYPE
from app.settings import settings

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class ImpersonationGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method not in _SAFE_METHODS:
            header = request.headers.get("Authorization", "")
            if header.lower().startswith("bearer "):
                token = header.split(" ", 1)[1]
                try:
                    payload = pyjwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
                except pyjwt.PyJWTError:
                    payload = None
                if payload is not None and payload.get("type") == IMPERSONATION_TOKEN_TYPE:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": {
                                "code": "FORBIDDEN",
                                "message": (
                                    "Impersonation sessions are read-only. "
                                    "Sign out of impersonation to make changes."
                                ),
                                "details": {},
                            }
                        },
                    )
        return await call_next(request)
