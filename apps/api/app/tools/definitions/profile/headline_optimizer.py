"""Headline Optimizer -- five headline variants grounded in the user's
own identity and experience, optionally tailored to a target role.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    target_role: str = Field(default="", title="Target role")


class _Variant(_StrictModel):
    text: str = Field(max_length=220)
    rationale: str
    keywords: list[str]
    audience: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=5, max_length=5)


DEFINITION = ToolDefinition(
    id="profile.headline_optimizer",
    hub=Hub.PROFILE,
    name="Headline Optimizer",
    short_description="Five LinkedIn headline variants grounded in your real experience.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.headline_optimizer.v1",
    required_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.TARGET_ROLE],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.HEADLINE,
)
