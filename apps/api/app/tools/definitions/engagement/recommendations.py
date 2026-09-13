"""Engagement Recommendations -- prioritised, reasoned actions for
where and how to engage, derived from the user's profile, industry,
and stated goals. Never outreach itself (no message is generated here),
so this is the one Engagement Hub tool that doesn't count toward the
outreach daily soft cap or gate behind the review checkbox. The prompt
carries an explicit, tested refusal of automation, pods, and
engagement-farming suggestions.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    industry: str = Field(default="", title="Industry")
    goals: str = Field(default="", title="Your stated goals")


class _Row(_StrictModel):
    action: str
    reason: str
    cadence: Literal["daily", "a few times a week", "weekly", "a few times a month"]


class _Output(_StrictModel):
    columns: list[str]
    rows: list[_Row] = Field(min_length=3, max_length=10)


DEFINITION = ToolDefinition(
    id="engagement.recommendations",
    hub=Hub.ENGAGEMENT,
    name="Engagement Recommendations",
    short_description="Prioritised, reasoned actions for where and how to engage -- never automation.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="engagement.recommendations.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
    ],
    result_renderer=ResultRenderer.TABLE,
)
