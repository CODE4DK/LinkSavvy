from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.career.schema import ResumeDocument


class ResumeParseResponse(BaseModel):
    """Returned by the paste/upload parse endpoints -- always a draft
    for the user to review and correct, never yet committed."""

    model_config = ConfigDict(extra="forbid")

    draft: ResumeDocument
    warnings: list[str]


class CommitResumeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    source: str
    document: ResumeDocument
    original_file_ref: str | None = None


class ResumeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    source: str
    parsed: ResumeDocument
    version: int
    is_active: bool
    ats_score: int | None
    created_at: datetime
    updated_at: datetime


class JobDescriptionParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    company: str | None = None
    raw_text: str


class JobDescriptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    company: str | None
    source: str
    raw_text: str
    parsed: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CreateResumeMatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_id: str
    job_description_id: str


class ResumeMatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    resume_id: str
    job_description_id: str
    overall_match: int
    component_scores: list[Any]
    matched: list[Any]
    missing: list[Any]
    transferable: list[Any]
    created_at: datetime
