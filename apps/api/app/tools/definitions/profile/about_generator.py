"""About Section Generator -- three About-section variants, each a
hook/body/CTA within LinkedIn's 2,600-character limit.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    target_role: str = Field(default="", title="Target role")
    user_supplied_text: str = Field(default="", title="Anything else to mention?")


class _Variant(_StrictModel):
    hook: str
    body: str = Field(max_length=2600)
    cta: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=3, max_length=3)


DEFINITION = ToolDefinition(
    id="profile.about_generator",
    hub=Hub.PROFILE,
    name="About Section Generator",
    short_description="Three About-section variants -- a hook, the body, and a call to action.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.about_generator.v1",
    required_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[
        ContextKey.PROFILE_SKILLS,
        ContextKey.TARGET_ROLE,
        ContextKey.USER_SUPPLIED_TEXT,
    ],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.ABOUT,
)
