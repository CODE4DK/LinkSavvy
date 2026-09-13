"""Connection Request Generator -- three connection notes, each hard-
capped at LinkedIn's 300-character connection note limit. An
over-length note is rejected by the gateway's own JSON Schema
validation (see app/ai/gateway.py), never silently truncated.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.engagement.guardrails import CONNECTION_NOTE_MAX_CHARS, make_variants_postprocessor
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    who_they_are: str = Field(
        title="Their headline or profile, pasted", json_schema_extra={"format": "textarea"}
    )
    how_you_know_them: str = Field(default="", title="How you know them or why you're reaching out")
    goal: str = Field(default="", title="Your goal for this connection")


class _Variant(_StrictModel):
    note: str = Field(max_length=CONNECTION_NOTE_MAX_CHARS)


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=3, max_length=3)


DEFINITION = ToolDefinition(
    id="engagement.connection_request",
    hub=Hub.ENGAGEMENT,
    name="Connection Request Generator",
    short_description="Three connection notes, each within LinkedIn's 300-character limit.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="engagement.connection_request.v1",
    optional_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.MESSAGE,
    counts_as_outreach=True,
    postprocess=make_variants_postprocessor(
        text_field="note", context_fields=["who_they_are", "how_you_know_them", "goal"]
    ),
)
