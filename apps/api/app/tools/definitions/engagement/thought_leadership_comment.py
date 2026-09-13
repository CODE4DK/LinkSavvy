"""Thought Leadership Comment -- one longer, substantive comment that
contributes a genuine insight, with an explicit "what this adds" field
the user can check before posting.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.engagement.guardrails import COMMENT_MAX_CHARS, make_variants_postprocessor
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    post_text: str = Field(title="Post to comment on", json_schema_extra={"format": "textarea"})
    your_angle: str = Field(default="", title="The insight or angle you want to contribute")


class _Variant(_StrictModel):
    comment: str = Field(max_length=COMMENT_MAX_CHARS)
    what_this_adds: str = Field(title="What this adds beyond the post itself")


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=1, max_length=1)


DEFINITION = ToolDefinition(
    id="engagement.thought_leadership_comment",
    hub=Hub.ENGAGEMENT,
    name="Thought Leadership Comment",
    short_description="One substantive comment that contributes a genuine insight.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="engagement.thought_leadership_comment.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
    ],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.COMMENT,
    counts_as_outreach=True,
    postprocess=make_variants_postprocessor(
        text_field="comment", context_fields=["post_text", "your_angle"]
    ),
)
