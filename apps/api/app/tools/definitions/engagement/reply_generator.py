"""Comment Reply Generator -- three replies at different warmth levels
to a comment left on the user's own post.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.engagement.guardrails import COMMENT_MAX_CHARS, make_variants_postprocessor
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition

_Relationship = Literal[
    "stranger",
    "new_connection",
    "colleague",
    "client_or_prospect",
    "mentor_or_mentee",
    "old_contact",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    original_post: str = Field(title="Your original post", json_schema_extra={"format": "textarea"})
    comment_text: str = Field(
        title="The comment you're replying to", json_schema_extra={"format": "textarea"}
    )
    relationship: _Relationship = Field(default="new_connection", title="Relationship")
    intent: str = Field(default="", title="What you want this reply to do")


class _Variant(_StrictModel):
    warmth: Literal["warm", "neutral", "brief"]
    reply: str = Field(max_length=COMMENT_MAX_CHARS)


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=3, max_length=3)


DEFINITION = ToolDefinition(
    id="engagement.reply_generator",
    hub=Hub.ENGAGEMENT,
    name="Comment Reply Generator",
    short_description="Three replies to a comment on your post, at different warmth levels.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="engagement.reply_generator.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
    ],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.COMMENT,
    counts_as_outreach=True,
    postprocess=make_variants_postprocessor(
        text_field="reply", context_fields=["original_post", "comment_text", "intent"]
    ),
)
