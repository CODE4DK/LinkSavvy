"""Direct Message Generator -- three messages for a stated goal. A
sales goal requires the prompt to disclose intent within the first two
sentences (see engagement.direct_message.v1.prompt.md); an optional
InMail-style subject is hard-capped at LinkedIn's 200-character limit.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.engagement.guardrails import INMAIL_SUBJECT_MAX_CHARS, make_variants_postprocessor
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    recipient_context: str = Field(
        title="Who they are / context about them", json_schema_extra={"format": "textarea"}
    )
    goal: Literal["advice", "referral", "collaboration", "sales", "hiring"] = Field(
        default="advice", title="Goal"
    )
    relationship_strength: Literal["stranger", "weak_tie", "acquaintance", "strong_tie"] = Field(
        default="weak_tie", title="Relationship strength"
    )


class _Variant(_StrictModel):
    subject: str | None = Field(default=None, max_length=INMAIL_SUBJECT_MAX_CHARS)
    message: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=3, max_length=3)


DEFINITION = ToolDefinition(
    id="engagement.direct_message",
    hub=Hub.ENGAGEMENT,
    name="Direct Message Generator",
    short_description="Three direct messages for a stated goal, sales pitches always disclosed upfront.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="engagement.direct_message.v1",
    optional_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.MESSAGE,
    counts_as_outreach=True,
    postprocess=make_variants_postprocessor(
        text_field="message", context_fields=["recipient_context", "goal"]
    ),
)
