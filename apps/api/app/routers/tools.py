"""The Tool Framework's public API. See app/tools/ for the definition
shape, the registry that discovers and validates tools, and the
context assembler every tool's prompt is built from.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import get_current_user
from app.models.user import User
from app.schemas.tools import ToolSummary
from app.tools.definition import Hub
from app.tools.presenters import to_tool_summary
from app.tools.registry import get_registry

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("", response_model=list[ToolSummary])
async def list_tools(
    hub: Hub | None = Query(default=None),
    _user: User = Depends(get_current_user),
) -> list[ToolSummary]:
    registry = get_registry()
    definitions = registry.by_hub(hub) if hub is not None else registry.all()
    return [to_tool_summary(definition) for definition in definitions]
