"""Profile Analysis -- a qualitative read of the whole profile: what's
working, what's weak, and what to fix next. Complements Phase 4's
deterministic Health Score rather than recomputing it; this tool never
produces a numeric score of its own.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    pass


class _Finding(_StrictModel):
    title: str
    severity: Literal["info", "warning", "critical"]
    description: str
    recommendation: str


class _Output(_StrictModel):
    summary: str
    findings: list[_Finding]


DEFINITION = ToolDefinition(
    id="profile.analysis",
    hub=Hub.PROFILE,
    name="Profile Analysis",
    short_description=(
        "A qualitative read of your whole profile -- what's working, what's weak, "
        "and what to fix next."
    ),
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.analysis.v1",
    required_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_ABOUT,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
    ],
    optional_context=[ContextKey.AUDIT_LATEST_FINDINGS],
    result_renderer=ResultRenderer.ANALYSIS,
    save_as=AssetType.ANALYSIS,
)
