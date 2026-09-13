"""Carousel Generator -- a cover, 5-12 slides, a closing CTA, and a
caption for a LinkedIn document-post carousel. Section 4's carousel
builder reads this structure directly (cover/slides/closing/caption)
to build a re-editable, exportable slide deck; the generic `thread`
renderer (apps/web/src/tools/renderers.tsx) shows the same structure
as a sequential preview inside the tool runner.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    topic: str = Field(title="Topic")
    slide_count: int = Field(default=8, ge=5, le=12, title="Number of slides")
    goal: str = Field(default="", title="Goal")


class _Cover(_StrictModel):
    headline: str
    subhead: str


class _Slide(_StrictModel):
    index: int
    headline: str
    body: str
    visual_note: str


class _Closing(_StrictModel):
    cta: str


class _Output(_StrictModel):
    cover: _Cover
    slides: list[_Slide] = Field(min_length=5, max_length=12)
    closing: _Closing
    caption: str


DEFINITION = ToolDefinition(
    id="content.carousel_generator",
    hub=Hub.CONTENT,
    name="Carousel Generator",
    short_description="A cover, slide-by-slide body, closing CTA, and caption for a document post.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.carousel_generator.v1",
    required_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.PROFILE_SKILLS, ContextKey.VOICE_PROFILE],
    result_renderer=ResultRenderer.THREAD,
    save_as=AssetType.CAROUSEL,
)
