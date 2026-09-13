"""Networking Recommendations -- who to build relationships with,
which communities and conversations to join, a realistic cadence, and
warm-intro paths through the user's own existing network. Deliberately
never produces named individuals, lead lists, scraped contacts, or a
bulk outreach plan -- see the prompt's explicit refusal rule and
tests/tools/definitions/test_growth_tools.py.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    industry: str = Field(default="", title="Industry")
    content_themes: str = Field(default="", title="Themes you post about")


class _Bullet(_StrictModel):
    text: str


class _Section(_StrictModel):
    heading: str
    body: str = ""
    bullets: list[_Bullet] = Field(default_factory=list)


class _Output(_StrictModel):
    sections: list[_Section] = Field(min_length=4, max_length=4)


DEFINITION = ToolDefinition(
    id="growth.networking_recommendations",
    hub=Hub.GROWTH,
    name="Networking Recommendations",
    short_description=(
        "Who to build relationships with, communities worth joining, a realistic cadence, "
        "and warm-intro paths through your own network -- never a lead list."
    ),
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="growth.networking_recommendations.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.TARGET_ROLE,
    ],
    result_renderer=ResultRenderer.DOCUMENT,
)
