"""Resume <-> JD Match -- an overall match percentage built from named,
weighted components, reconstructible by summing each component's own
contribution (weight * score). `postprocess` derives the generic
`columns`/`rows` shape the `table` renderer expects from `matched`/
`missing`/`transferable` -- the AI never has to know about that shape,
it only ever returns the real structured breakdown.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    resume_text: str = Field(title="Resume text", json_schema_extra={"format": "textarea"})
    job_description_text: str = Field(
        title="Job description text", json_schema_extra={"format": "textarea"}
    )


_Component = Literal[
    "hard_requirements", "preferred_requirements", "keyword_coverage", "seniority_fit", "domain_fit"
]


class _ComponentScore(_StrictModel):
    component: _Component
    weight: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=100.0)
    contribution: float = Field(ge=0.0, le=100.0)


class _MatchedItem(_StrictModel):
    requirement: str
    evidence: str = Field(title="Where the resume shows this")


class _MissingItem(_StrictModel):
    requirement: str
    learnable: bool = Field(title="Learnable on the job, vs. a hard blocker")


class _TransferableItem(_StrictModel):
    requirement: str
    resume_experience: str = Field(title="The resume experience this maps to")


class _Output(_StrictModel):
    overall_match: int = Field(ge=0, le=100)
    component_scores: list[_ComponentScore] = Field(min_length=5, max_length=5)
    matched: list[_MatchedItem]
    missing: list[_MissingItem]
    transferable: list[_TransferableItem]


def _postprocess(output: dict[str, Any], _raw_input: dict[str, Any]) -> dict[str, Any]:
    columns = ["requirement", "status", "detail"]
    rows: list[dict[str, str]] = []
    for item in output.get("matched", []):
        rows.append(
            {"requirement": item["requirement"], "status": "matched", "detail": item["evidence"]}
        )
    for item in output.get("missing", []):
        detail = "learnable" if item.get("learnable") else "hard blocker"
        rows.append({"requirement": item["requirement"], "status": "missing", "detail": detail})
    for item in output.get("transferable", []):
        rows.append(
            {
                "requirement": item["requirement"],
                "status": "transferable",
                "detail": item["resume_experience"],
            }
        )
    return {**output, "columns": columns, "rows": rows}


DEFINITION = ToolDefinition(
    id="career.resume_jd_match",
    hub=Hub.CAREER,
    name="Resume <-> JD Match",
    short_description="An overall match percentage built from named, weighted components.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="career.resume_jd_match.v1",
    optional_context=[ContextKey.PROFILE_IDENTITY],
    result_renderer=ResultRenderer.TABLE,
    postprocess=_postprocess,
)
