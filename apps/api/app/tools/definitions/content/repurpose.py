"""Repurpose -- turns an existing asset into a different content format
(post -> carousel, carousel -> post, post -> comment-starter, experience
bullet -> post). The output is always shaped as `document` sections so
one schema covers every target format; the source content itself is
never altered, only reformatted.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    source_content: str = Field(title="Existing content", json_schema_extra={"format": "textarea"})
    source_format: Literal["post", "carousel", "experience_bullet"] = Field(
        default="post", title="Current format"
    )
    target_format: Literal["post", "carousel", "comment_starter"] = Field(
        default="post", title="Target format"
    )


class _Bullet(_StrictModel):
    text: str


class _Section(_StrictModel):
    heading: str
    body: str = ""
    bullets: list[_Bullet] = Field(default_factory=list)


class _Output(_StrictModel):
    sections: list[_Section] = Field(min_length=1, max_length=14)


DEFINITION = ToolDefinition(
    id="content.repurpose",
    hub=Hub.CONTENT,
    name="Repurpose",
    short_description="Turns an existing post, carousel, or bullet into a different content format.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.repurpose.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
        ContextKey.VOICE_PROFILE,
    ],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as=AssetType.TEMPLATE,
)
