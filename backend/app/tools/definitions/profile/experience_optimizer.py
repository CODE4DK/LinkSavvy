"""Experience Optimizer -- rewrites the description and achievement
bullets for the user's current (or most recent) role. A bullet is
flagged when it would be stronger with a real metric only the user
knows -- the AI never invents one.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    user_supplied_text: str = Field(
        default="", title="Anything specific to include, like a metric?"
    )


class _Bullet(_StrictModel):
    text: str
    flagged: bool
    flag_reason: str | None = None


class _Section(_StrictModel):
    heading: str
    body: str
    bullets: list[_Bullet] = Field(min_length=3, max_length=6)


class _Output(_StrictModel):
    sections: list[_Section] = Field(min_length=1, max_length=1)


DEFINITION = ToolDefinition(
    id="profile.experience_optimizer",
    hub=Hub.PROFILE,
    name="Experience Optimizer",
    short_description="Rewrites your current role's description and achievement bullets.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.experience_optimizer.v1",
    required_context=[ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.USER_SUPPLIED_TEXT],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as=AssetType.EXPERIENCE_BULLETS,
)
