"""Comment Generator -- four comments on a pasted post, each taking a
distinct stance and grounded in the user's own expertise, with a
one-line note on what each adds to the conversation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.engagement.guardrails import COMMENT_MAX_CHARS, make_variants_postprocessor
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition

_Stance = Literal[
    "agree_and_extend", "respectful_pushback", "ask_a_question", "share_experience", "add_data"
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    post_text: str = Field(title="Post to comment on", json_schema_extra={"format": "textarea"})
    angle: str = Field(default="", title="Your angle")
    stance: _Stance = Field(default="agree_and_extend", title="Desired stance")
    length: Literal["short", "medium", "long"] = Field(default="medium", title="Length")


class _Variant(_StrictModel):
    stance: _Stance
    comment: str = Field(max_length=COMMENT_MAX_CHARS)
    adds: str = Field(title="What this adds to the conversation")


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=4, max_length=4)


DEFINITION = ToolDefinition(
    id="engagement.comment_generator",
    hub=Hub.ENGAGEMENT,
    name="Comment Generator",
    short_description="Four comments on a post, each taking a distinct stance.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="engagement.comment_generator.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
    ],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.COMMENT,
    counts_as_outreach=True,
    postprocess=make_variants_postprocessor(
        text_field="comment", context_fields=["post_text", "angle"]
    ),
)
