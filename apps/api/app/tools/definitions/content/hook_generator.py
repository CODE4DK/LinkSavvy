"""Hook Generator -- ten opening lines across distinct hook patterns,
each with a fold-preview showing exactly what a reader sees above
LinkedIn's "see more" cut.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    topic: str = Field(title="Topic or raw idea")
    post_type: Literal[
        "story", "insight", "how-to", "announcement", "opinion", "case study", "list"
    ] = Field(default="insight", title="Post type")


class _Variant(_StrictModel):
    pattern: Literal["question", "contrarian", "number", "story-open", "confession", "observation"]
    hook: str
    fold_preview: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=10, max_length=10)


DEFINITION = ToolDefinition(
    id="content.hook_generator",
    hub=Hub.CONTENT,
    name="Hook Generator",
    short_description="Ten opening lines across distinct hook patterns, each with a fold preview.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.hook_generator.v1",
    required_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.PROFILE_SKILLS, ContextKey.VOICE_PROFILE],
    result_renderer=ResultRenderer.VARIANTS,
)
