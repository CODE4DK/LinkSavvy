"""Skills Analyzer -- ranks the user's listed skills against their
experience (and, optionally, a target role) into have/low-value/missing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    target_role: str = Field(default="", title="Target role")


class _Row(_StrictModel):
    skill: str
    status: Literal["have", "low-value", "missing"]
    relevance: Literal["high", "medium", "low"]
    note: str


class _Output(_StrictModel):
    columns: list[str]
    rows: list[_Row]


DEFINITION = ToolDefinition(
    id="profile.skills_analyzer",
    hub=Hub.PROFILE,
    name="Skills Analyzer",
    short_description="Ranks your listed skills by relevance and flags what's missing.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.skills_analyzer.v1",
    required_context=[ContextKey.PROFILE_SKILLS, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.TARGET_ROLE],
    result_renderer=ResultRenderer.TABLE,
    save_as=AssetType.ANALYSIS,
)
