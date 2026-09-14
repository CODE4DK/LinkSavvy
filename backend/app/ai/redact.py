"""Scrubs free text out of anything that might end up in a log line.

The gateway's structured invocation log (see `app/ai/gateway.py`'s
`_record_invocation`) never includes a prompt body or user content by
construction — it only ever carries a fixed set of structural fields
(correlation id, prompt id/version, tier, provider, model, token counts,
cost, latency, outcome). This module is the safety net for the one place
that can't make the same guarantee: an exception's message. A vendor's
HTTP error body occasionally echoes back a fragment of the request that
triggered it (a content-moderation rejection quoting the flagged text,
for instance), so anything derived from `str(exc)` gets redacted before
it's logged.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# Keys that plausibly carry user-supplied or model-generated free text,
# checked case-insensitively. Structural/numeric fields (ids, counts,
# timestamps, enums) are never in this set and pass through untouched.
_TEXT_BEARING_KEYS = {
    "text",
    "content",
    "message",
    "prompt",
    "rendered",
    "context",
    "body",
    "delta",
    "error",
    "detail",
}


def redact_text(value: str) -> str:
    """Never returns the value itself, or even a prefix of it — only its
    length, which is enough to tell "something changed" apart from
    "nothing happened" in a log line without repeating what was said."""
    return f"<redacted:{len(value)} chars>"


def redact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively redacts any key that looks like it carries free text.
    Used to sanitize a diagnostic payload (an exception's `args`, a debug
    dump of a request/response) before it's logged."""
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in _TEXT_BEARING_KEYS and isinstance(value, str):
            result[key] = redact_text(value)
        elif isinstance(value, Mapping):
            result[key] = redact_mapping(value)
        elif isinstance(value, list):
            result[key] = [
                redact_mapping(item) if isinstance(item, Mapping) else item for item in value
            ]
        else:
            result[key] = value
    return result
