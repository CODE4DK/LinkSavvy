"""Career Roadmap Generator -- phased milestones with skills to build,
evidence to create, people to learn from, and LinkedIn actions per
phase, each tied back to a LinkSavvy tool. Shaped as `document`
sections (one per phase) with no new renderer needed.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    current_role: str = Field(title="Current role")
    target_role: str = Field(title="Target role")
    time_horizon: str = Field(default="12 months", title="Time horizon")
    constraints: str = Field(default="", title="Constraints (time, budget, location, etc.)")


class _Bullet(_StrictModel):
    text: str
    flagged: bool = False
    flag_reason: str | None = None


class _Phase(_StrictModel):
    heading: str
    body: str = ""
    bullets: list[_Bullet] = Field(min_length=4)


class _Output(_StrictModel):
    sections: list[_Phase] = Field(min_length=2, max_length=5)


DEFINITION = ToolDefinition(
    id="career.roadmap",
    hub=Hub.CAREER,
    name="Career Roadmap Generator",
    short_description="Phased milestones from your current role to your target role.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="career.roadmap.v1",
    required_context=[ContextKey.TARGET_ROLE],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as=AssetType.ROADMAP,
)
