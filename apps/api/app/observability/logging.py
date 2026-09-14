"""Structured (JSON) logging with a per-request correlation id threaded
through every log line emitted while handling that request -- what makes
it possible to pull every log line for one failing request out of a
shared log stream. See docs/performance.md "Structured logging and
tracing" and docs/runbook.md for how this is used during an incident.

This does not replace the AI gateway's own `correlation_id` (see
app/ai/gateway.py), which identifies one AI invocation and can outlive a
single HTTP request (retries, background jobs) -- the two are unrelated
ids serving different scopes, and a log line inside an AI call carries
both.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import uuid
from datetime import UTC, datetime

REQUEST_ID_HEADER = "X-Request-ID"

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

# The standard attributes every LogRecord carries -- anything else on a
# record came from a call's `extra={...}` and belongs in the JSON output.
_STANDARD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


def new_request_id() -> str:
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> contextvars.Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id is not None:
            payload["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(*, level: int = logging.INFO) -> None:
    """Call once at process startup (API and worker both). Idempotent --
    safe to call again in a test fixture without stacking handlers."""
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
