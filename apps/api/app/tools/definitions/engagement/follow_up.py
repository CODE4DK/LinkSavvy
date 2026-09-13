"""Follow-Up Message Generator -- three follow-ups with an explicit
no-guilt tone and a graceful exit line, for reaching back out after a
gap in contact.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.engagement.guardrails import make_variants_postprocessor
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    prior_context: str = Field(
        title="What happened before (prior conversation, connection, etc.)",
        json_schema_extra={"format": "textarea"},
    )
    time_since_last_contact: Literal[
        "a few days", "1-2 weeks", "3-4 weeks", "1-3 months", "3+ months"
    ] = Field(default="1-2 weeks", title="Time since last contact")
    purpose: str = Field(default="", title="What you're following up about")


class _Variant(_StrictModel):
    message: str
    exit_line: str = Field(title="A graceful, no-guilt way to end it")


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=3, max_length=3)


DEFINITION = ToolDefinition(
    id="engagement.follow_up",
    hub=Hub.ENGAGEMENT,
    name="Follow-Up Message Generator",
    short_description="Three no-guilt follow-ups, each with a graceful exit line.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="engagement.follow_up.v1",
    optional_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.MESSAGE,
    counts_as_outreach=True,
    postprocess=make_variants_postprocessor(
        text_field="message", context_fields=["prior_context", "purpose"]
    ),
)
