"""Post Generator -- three full post variants from a topic or raw idea,
each with a hook, body, CTA, hashtags, an estimated read time, and a
one-line note on why the hook works.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    topic: str = Field(title="Topic or raw idea")
    post_type: Literal[
        "story", "insight", "how-to", "announcement", "opinion", "case study", "list"
    ] = Field(default="insight", title="Post type")
    audience: str = Field(default="", title="Audience")
    tone: str = Field(default="", title="Tone")
    length: Literal["short", "standard", "long"] = Field(default="standard", title="Length")
    include_cta: bool = Field(default=True, title="Include a call to action")
    include_hashtags: bool = Field(default=True, title="Include hashtags")


class _Variant(_StrictModel):
    hook: str
    body: str = Field(max_length=3000)
    cta: str
    hashtags: list[str]
    estimated_read_time_seconds: int = Field(ge=1)
    hook_rationale: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=3, max_length=3)


DEFINITION = ToolDefinition(
    id="content.post_generator",
    hub=Hub.CONTENT,
    name="Post Generator",
    short_description="Three full post variants from a topic, grounded in your real experience.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.post_generator.v1",
    required_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.PROFILE_SKILLS, ContextKey.VOICE_PROFILE],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.POST,
)
