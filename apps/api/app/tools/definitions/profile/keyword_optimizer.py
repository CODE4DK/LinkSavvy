"""Keyword Optimizer -- prioritised keywords the profile should surface
for search, with whether each is already present and where to place it.
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
    keyword: str
    priority: Literal["high", "medium", "low"]
    coverage: Literal["present", "missing"]
    placement: str


class _Output(_StrictModel):
    columns: list[str]
    rows: list[_Row]


DEFINITION = ToolDefinition(
    id="profile.keyword_optimizer",
    hub=Hub.PROFILE,
    name="Keyword Optimizer",
    short_description="Prioritised keywords your profile should surface, and where to place them.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.keyword_optimizer.v1",
    required_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
    ],
    optional_context=[ContextKey.TARGET_ROLE],
    result_renderer=ResultRenderer.TABLE,
    save_as=AssetType.ANALYSIS,
)
