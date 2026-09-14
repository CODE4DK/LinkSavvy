"""Post Rewriter -- rewrites an existing post toward a stated goal, with
a change list explaining each edit.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    post_body: str = Field(title="Existing post", json_schema_extra={"format": "textarea"})
    goal: Literal["tighter", "warmer", "more authoritative", "more concrete", "restructure"] = (
        Field(default="tighter", title="Goal")
    )


class _ChangeBullet(_StrictModel):
    text: str
    flagged: bool = False
    flag_reason: str | None = None


class _Section(_StrictModel):
    heading: str
    body: str = ""
    bullets: list[_ChangeBullet] = Field(default_factory=list)


class _Output(_StrictModel):
    sections: list[_Section] = Field(min_length=2, max_length=2)


DEFINITION = ToolDefinition(
    id="content.post_rewriter",
    hub=Hub.CONTENT,
    name="Post Rewriter",
    short_description="Rewrites an existing post toward a stated goal, with a change list.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="content.post_rewriter.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
        ContextKey.VOICE_PROFILE,
    ],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as=AssetType.POST,
)
