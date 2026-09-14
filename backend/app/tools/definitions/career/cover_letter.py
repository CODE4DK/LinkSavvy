"""Cover Letter Generator -- cites only real experience from the
resume, with a shorter email version alongside the full letter.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    resume_text: str = Field(title="Resume text", json_schema_extra={"format": "textarea"})
    job_description_text: str = Field(
        title="Job description text", json_schema_extra={"format": "textarea"}
    )
    tone: Literal["formal", "warm", "confident", "conversational"] = Field(
        default="confident", title="Tone"
    )
    length: Literal["short", "medium", "long"] = Field(default="medium", title="Length")
    emphasize: str = Field(default="", title="Anything you want emphasised")


class _Section(_StrictModel):
    heading: str
    body: str


class _Output(_StrictModel):
    sections: list[_Section] = Field(min_length=2, max_length=2)


DEFINITION = ToolDefinition(
    id="career.cover_letter",
    hub=Hub.CAREER,
    name="Cover Letter Generator",
    short_description="A cover letter citing only real resume experience, plus a shorter email version.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="career.cover_letter.v1",
    optional_context=[ContextKey.PROFILE_IDENTITY],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as=AssetType.COVER_LETTER,
)
