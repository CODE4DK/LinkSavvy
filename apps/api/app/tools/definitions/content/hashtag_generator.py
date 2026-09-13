"""Hashtag Generator -- tiered hashtags (broad, niche, community) for an
existing post, capped at a sensible number with an explicit warning
against hashtag stuffing.
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
    industry: str = Field(default="", title="Industry")


class _Row(_StrictModel):
    tier: Literal["broad", "niche", "community"]
    hashtag: str
    note: str


class _Output(_StrictModel):
    columns: list[str]
    rows: list[_Row] = Field(min_length=3, max_length=8)
    stuffing_warning: str


DEFINITION = ToolDefinition(
    id="content.hashtag_generator",
    hub=Hub.CONTENT,
    name="Hashtag Generator",
    short_description="Tiered hashtags for a post -- broad, niche, and community -- capped and never stuffed.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.hashtag_generator.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
        ContextKey.VOICE_PROFILE,
    ],
    result_renderer=ResultRenderer.TABLE,
)
