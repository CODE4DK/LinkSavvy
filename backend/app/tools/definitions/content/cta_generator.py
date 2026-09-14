"""CTA Generator -- six calls to action for an existing post, graded by
how demanding they are of the reader.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    post_body: str = Field(title="Post body", json_schema_extra={"format": "textarea"})
    goal: Literal["comments", "dms", "profile_visits", "link_clicks", "follows"] = Field(
        default="comments", title="Goal"
    )


class _Variant(_StrictModel):
    text: str
    demand_level: Literal["low", "medium", "high"]
    rationale: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=6, max_length=6)


DEFINITION = ToolDefinition(
    id="content.cta_generator",
    hub=Hub.CONTENT,
    name="CTA Generator",
    short_description="Six calls to action for a post, graded from low to high demand on the reader.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.cta_generator.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
        ContextKey.VOICE_PROFILE,
    ],
    result_renderer=ResultRenderer.VARIANTS,
)
