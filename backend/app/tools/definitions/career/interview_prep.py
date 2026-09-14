"""Interview Preparation Assistant -- likely questions grouped by type,
each with what the interviewer is really assessing and a STAR scaffold
drawn from the user's own experience, plus questions the candidate
should ask. Shaped as a `thread` so the generic ToolRunner needs no
new renderer: each question is one "interviewer" message, and the
candidate's own questions close the thread.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    job_description_text: str = Field(
        title="Job description text", json_schema_extra={"format": "textarea"}
    )
    interview_type: Literal["screen", "technical", "behavioural", "panel", "final"] = Field(
        default="screen", title="Interview type"
    )
    seniority: str = Field(default="", title="Seniority")
    resume_text: str = Field(
        default="",
        title="Resume text (for STAR scaffolds)",
        json_schema_extra={"format": "textarea"},
    )


class _Message(_StrictModel):
    role: Literal["interviewer", "candidate"]
    text: str


class _Output(_StrictModel):
    messages: list[_Message] = Field(min_length=6, max_length=11)


DEFINITION = ToolDefinition(
    id="career.interview_prep",
    hub=Hub.CAREER,
    name="Interview Preparation Assistant",
    short_description="Likely questions with STAR scaffolds from your own experience, plus questions to ask.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="career.interview_prep.v1",
    optional_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    result_renderer=ResultRenderer.THREAD,
    save_as=AssetType.CONVERSATION,
)
