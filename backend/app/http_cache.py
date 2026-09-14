"""Conditional GET (ETag) support for read-heavy, rarely-changing
endpoints. Not a general-purpose caching layer -- FastAPI has no native
conditional-request handling, so each endpoint that wants this calls
`etag_or_none` explicitly and returns its bare 304 itself; see
`app/routers/tools.py::list_tools` for the pattern.
"""

from __future__ import annotations

import hashlib
import json

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response as PlainResponse


def compute_etag(payload: object) -> str:
    body = json.dumps(jsonable_encoder(payload), sort_keys=True, default=str).encode()
    return f'"{hashlib.sha256(body).hexdigest()[:32]}"'


def etag_or_none(request: Request, response: Response, payload: object) -> Response | None:
    """Sets the response's ETag/Cache-Control headers for `payload` and,
    if the client's `If-None-Match` already matches, returns a bare 304
    the caller should return immediately instead of the full body.
    Returns None when the caller should proceed and return `payload`
    normally (the just-set headers still apply to that response)."""
    tag = compute_etag(payload)
    response.headers["ETag"] = tag
    response.headers["Cache-Control"] = "private, max-age=0, must-revalidate"
    if request.headers.get("if-none-match") == tag:
        return PlainResponse(status_code=304, headers=response.headers)
    return None
