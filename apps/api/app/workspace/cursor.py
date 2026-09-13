"""An opaque list cursor that can hold either shape a listing needs:
`before_id` for the default listing, or `offset` for a relevance-ordered
search result where there's no stable column to key off of.
"""

from __future__ import annotations

import base64
import json
import uuid
from typing import Any


def encode_cursor(payload: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_cursor(cursor: str) -> dict[str, Any]:
    try:
        data: dict[str, Any] = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception as exc:  # noqa: BLE001 -- any malformed cursor is the same "bad request"
        raise ValueError("invalid cursor") from exc
    return data


def encode_before_id(asset_id: uuid.UUID) -> str:
    # Ordering and paginating by `id` alone (a UUIDv7, itself
    # monotonically time-ordered) rather than by `created_at` sidesteps
    # a real trap: `created_at` is written by the database's own
    # `CURRENT_TIMESTAMP` (no fractional seconds) but a bound datetime
    # parameter round-tripped through Python serializes *with*
    # fractional seconds, so `created_at = :cursor_value` silently never
    # matches on SQLite -- `id` has no such format mismatch and is
    # already unique, so no tie-breaker is even needed.
    return encode_cursor({"before_id": str(asset_id)})


def encode_offset(offset: int) -> str:
    return encode_cursor({"offset": offset})
