"""`ToolDefinition` -- the one declaration a hub tool needs.

A tool is data, not code: `app/routers/tools.py`'s run endpoint, the
context assembler, and the web app's `<ToolRunner>` all key off this
shape and never off a tool's id. Adding a tool means adding a
definition file and a prompt -- never touching any of the three.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.tools.context import ContextKey

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User


class Hub(StrEnum):
    PROFILE = "profile"
    CONTENT = "content"
    ENGAGEMENT = "engagement"
    CAREER = "career"
    GROWTH = "growth"


class Plan(StrEnum):
    FREE = "free"
    PRO = "pro"


class ResultRenderer(StrEnum):
    VARIANTS = "variants"
    DOCUMENT = "document"
    ANALYSIS = "analysis"
    TABLE = "table"
    CALENDAR = "calendar"
    THREAD = "thread"


class AssetType(StrEnum):
    POST = "post"
    HEADLINE = "headline"
    ABOUT = "about"
    EXPERIENCE_BULLETS = "experience_bullets"
    COMMENT = "comment"
    MESSAGE = "message"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    JOB_DESCRIPTION = "job_description"
    ANALYSIS = "analysis"
    CONVERSATION = "conversation"
    TEMPLATE = "template"
    CAROUSEL = "carousel"
    ROADMAP = "roadmap"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    id: str
    hub: Hub
    name: str
    short_description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    prompt_id: str
    required_context: list[ContextKey] = field(default_factory=list)
    optional_context: list[ContextKey] = field(default_factory=list)
    min_plan: Plan = Plan.FREE
    quota_metric: str = "tool_runs"
    result_renderer: ResultRenderer = ResultRenderer.DOCUMENT
    save_as: AssetType | None = None
    free_daily_cap: int | None = None
    supports_streaming: bool = False
    # An escape hatch for context a ContextKey can't express because it
    # isn't profile data at all -- e.g. wrapping a deterministic engine's
    # own output (Completeness Checker wraps Phase 2's `compute_completeness`
    # this way). Returns flat template vars already labelled the way
    # `assemble()` labels its own blocks; merged in after assembly, exempt
    # from token-budget trimming since it's small and never optional.
    precompute: Callable[[User, AsyncSession], Awaitable[dict[str, str]]] | None = None
