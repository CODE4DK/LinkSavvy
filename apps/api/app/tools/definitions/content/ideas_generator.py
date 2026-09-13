"""Content Ideas Generator -- 10-20 post ideas grounded in the user's
real experience, each ready to be sent straight into the calendar.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    how_many: int = Field(default=10, ge=10, le=20, title="How many ideas")
    themes_to_avoid: list[str] = Field(default_factory=list, title="Themes to avoid")
    time_horizon: str = Field(default="the next few weeks", title="Time horizon")


class _Row(_StrictModel):
    title: str
    angle: str
    post_type: Literal[
        "story", "insight", "how-to", "announcement", "opinion", "case study", "list"
    ]
    why: str
    difficulty: Literal["easy", "medium", "hard"]


class _Output(_StrictModel):
    columns: list[str]
    rows: list[_Row] = Field(min_length=10, max_length=20)


DEFINITION = ToolDefinition(
    id="content.ideas_generator",
    hub=Hub.CONTENT,
    name="Content Ideas Generator",
    short_description="10-20 post ideas grounded in your real experience, ready for the calendar.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.ideas_generator.v1",
    required_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.PROFILE_SKILLS, ContextKey.VOICE_PROFILE],
    result_renderer=ResultRenderer.TABLE,
)
