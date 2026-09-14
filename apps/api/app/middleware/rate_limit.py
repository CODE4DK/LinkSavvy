"""General-purpose API rate limiting: per-IP, per-user, and per-endpoint-
class token buckets, checked in that order on every request. In-memory
and per-process on purpose -- like app/ai/circuit_breaker.py, this is a
hint about what *this process* has seen recently, not durable state, and
adding Redis just to share it across workers would violate CLAUDE.md's
"MySQL is the sole datastore" rule for a feature whose worst failure mode
(a burst that briefly gets through on a fresh worker) is cheap. Real
multi-worker deployments should sit this behind an edge/gateway limiter
for the belt-and-suspenders case; see docs/security.md.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import jwt as pyjwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.security.jwt import ALGORITHM
from app.settings import settings


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class TokenBucketLimiter:
    """Classic token bucket: `capacity` tokens, refilled at `per_second`
    tokens/sec, one bucket per key. `allow()` both checks and consumes."""

    def __init__(self, *, capacity: int, per_second: float) -> None:
        self.capacity = capacity
        self.per_second = per_second
        self._buckets: dict[str, _Bucket] = {}

    def allow(self, key: str) -> tuple[bool, float]:
        now = time.monotonic()
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(tokens=float(self.capacity), last_refill=now)
            self._buckets[key] = bucket

        elapsed = now - bucket.last_refill
        bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.per_second)
        bucket.last_refill = now

        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return True, 0.0

        retry_after = (1 - bucket.tokens) / self.per_second
        return False, retry_after

    def reset(self) -> None:
        """Test-only: clears all bucket state between test cases."""
        self._buckets.clear()


# Endpoint classes, from tightest to loosest. A request matches the first
# prefix it starts with; anything unmatched falls into "default".
_ENDPOINT_CLASSES: list[tuple[str, str]] = [
    ("/api/v1/auth", "auth"),
    ("/api/v1/admin", "admin"),
    ("/api/v1/assistant", "ai"),
    ("/api/v1/tools", "ai"),
    ("/api/v1/billing/webhooks", "webhook"),
]

_CLASS_LIMITS: dict[str, tuple[int, float]] = {
    # (burst capacity, sustained tokens/second)
    "auth": (10, 10 / 60),  # 10 burst, ~1 every 6s sustained
    "ai": (20, 30 / 60),  # 20 burst, 30/min sustained
    "admin": (60, 120 / 60),
    "webhook": (100, 200 / 60),  # providers retry aggressively; don't punish them
    "default": (60, 120 / 60),
}

_ip_limiters: dict[str, TokenBucketLimiter] = {
    cls: TokenBucketLimiter(capacity=capacity, per_second=rate)
    for cls, (capacity, rate) in _CLASS_LIMITS.items()
}
# Per-user buckets get roughly double the per-IP allowance for the same
# class -- a shared office IP shouldn't starve individually-identified
# users of it, but an unauthenticated caller only ever gets the IP bucket.
_user_limiters: dict[str, TokenBucketLimiter] = {
    cls: TokenBucketLimiter(capacity=capacity * 2, per_second=rate * 2)
    for cls, (capacity, rate) in _CLASS_LIMITS.items()
}


def _endpoint_class(path: str) -> str:
    for prefix, cls in _ENDPOINT_CLASSES:
        if path.startswith(prefix):
            return cls
    return "default"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _user_id_from_request(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1]
    try:
        payload = pyjwt.decode(
            token, settings.jwt_secret, algorithms=[ALGORITHM], options={"verify_exp": False}
        )
    except pyjwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return str(sub) if sub else None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path == "/health" or request.url.path == "/ready":
            return await call_next(request)

        endpoint_class = _endpoint_class(request.url.path)
        ip = _client_ip(request)
        ip_limiter = _ip_limiters[endpoint_class]
        allowed, retry_after = ip_limiter.allow(f"ip:{ip}")
        if not allowed:
            return _too_many_requests(retry_after)

        user_id = _user_id_from_request(request)
        if user_id:
            user_limiter = _user_limiters[endpoint_class]
            allowed, retry_after = user_limiter.allow(f"user:{user_id}")
            if not allowed:
                return _too_many_requests(retry_after)

        return await call_next(request)


def _too_many_requests(retry_after: float) -> JSONResponse:
    seconds = max(1, int(retry_after) + 1)
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(seconds)},
        content={
            "error": {
                "code": "RATE_LIMITED",
                "message": "Too many requests. Please slow down and try again shortly.",
                "details": {"retry_after_seconds": seconds},
            }
        },
    )
