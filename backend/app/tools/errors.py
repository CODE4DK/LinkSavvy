"""Tool-framework errors, mirroring app/ai/prompts/models.py's split:
`ToolDefinitionError` is raised at load time for a malformed definition
or a definition/prompt mismatch and never reaches a request (the
registry lets it propagate so a bad tool fails application startup,
not the first request that happens to use it); `ToolNotFound` is a
runtime `ApiError` for an unknown or unpublished tool id.
"""

from __future__ import annotations

from app.errors import ApiError, ErrorCode


class ToolDefinitionError(Exception):
    pass


class ToolNotFound(ApiError):
    def __init__(self, tool_id: str) -> None:
        super().__init__(ErrorCode.NOT_FOUND, f"no tool registered with id {tool_id!r}")
