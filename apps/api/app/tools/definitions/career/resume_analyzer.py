"""Resume Analyzer -- a scored assessment across impact, clarity,
quantification, relevance, formatting, and length, with per-bullet
feedback. Deterministic checks (length, bullet count, weak verbs,
metric density, date gaps) run before the AI pass and are labelled
`rule_based: true` (see app/career/analysis.py's postprocess) so the
user can tell which findings are objective and which are the AI's
judgement.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.career.analysis import analyzer_postprocess
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    resume_text: str = Field(title="Resume text", json_schema_extra={"format": "textarea"})


class _DimensionScore(_StrictModel):
    dimension: Literal["impact", "clarity", "quantification", "relevance", "formatting", "length"]
    score: int = Field(ge=0, le=10)
    note: str


class _Finding(_StrictModel):
    title: str
    severity: Literal["info", "warning", "critical"]
    description: str
    recommendation: str | None = None


class _Output(_StrictModel):
    summary: str
    score: int = Field(ge=0, le=100)
    dimension_scores: list[_DimensionScore] = Field(min_length=6, max_length=6)
    findings: list[_Finding]


DEFINITION = ToolDefinition(
    id="career.resume_analyzer",
    hub=Hub.CAREER,
    name="Resume Analyzer",
    short_description="A scored assessment of your resume, with rule-based and AI findings kept separate.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="career.resume_analyzer.v1",
    optional_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    result_renderer=ResultRenderer.ANALYSIS,
    save_as=AssetType.ANALYSIS,
    postprocess=analyzer_postprocess,
)
