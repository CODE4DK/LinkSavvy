"""ATS Optimization -- primarily deterministic (see
app/career/ats_checks.py, wired in as `postprocess`): tables, multi-
column layouts, non-standard headings, special characters, file
naming, and missing keywords are all flagged by rule, never by the AI.
The AI is used only to suggest natural keyword placement, and its
prompt explicitly refuses to add a skill the resume doesn't already
show.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.career.ats_checks import ats_optimizer_postprocess
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    resume_text: str = Field(title="Resume text", json_schema_extra={"format": "textarea"})
    job_description_text: str = Field(
        default="",
        title="Target job description (optional)",
        json_schema_extra={"format": "textarea"},
    )
    file_name: str = Field(default="", title="File name (optional)")
    detected_two_column_layout: bool = Field(
        default=False, title="Two-column layout was detected on upload"
    )


class _KeywordSuggestion(_StrictModel):
    keyword: str
    suggested_placement: str = Field(
        title="Where in the resume this keyword could naturally fit, given real experience shown"
    )


class _Output(_StrictModel):
    keyword_suggestions: list[_KeywordSuggestion]


DEFINITION = ToolDefinition(
    id="career.ats_optimizer",
    hub=Hub.CAREER,
    name="ATS Optimization",
    short_description="Deterministic ATS-parseability checks, plus AI keyword-placement suggestions only.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="career.ats_optimizer.v1",
    result_renderer=ResultRenderer.ANALYSIS,
    save_as=AssetType.ANALYSIS,
    postprocess=ats_optimizer_postprocess,
)
