"""Resume Builder -- AI-assisted drafting, one section at a time. The
structural side of "building a resume" (starting from a ProfileSnapshot
or from scratch, three ATS-safe templates, live preview, PDF/DOCX
export) is deterministic code (app/career/service.py,
app/career/export.py), not an AI call -- this tool is only the part
that's genuinely generative: turning what the user tells it about one
section into a few draftable options.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    section: Literal["summary", "experience_bullets", "skills_list"] = Field(
        default="summary", title="Section to draft"
    )
    context_text: str = Field(
        title="Tell it about this section (role, company, achievements, etc.)",
        json_schema_extra={"format": "textarea"},
    )


class _Variant(_StrictModel):
    text: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=3, max_length=3)


DEFINITION = ToolDefinition(
    id="career.resume_builder",
    hub=Hub.CAREER,
    name="Resume Builder",
    short_description="AI-assisted drafting for one resume section at a time.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="career.resume_builder.v1",
    optional_context=[
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
    ],
    result_renderer=ResultRenderer.VARIANTS,
)
