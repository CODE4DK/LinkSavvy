"""The canonical ProfileSnapshot.

Every capture of a user's professional data — from LinkedIn's API, a
pasted profile, an uploaded resume, or the manual form — is normalised
into exactly this shape before it is ever stored or compared. Every
field is optional: `None` means "we don't know", `[]` means "we know
there are none", and `""` means "we were told it's blank" — those three
are never conflated. `field_provenance` records, per JSON-pointer-style
path, where a value came from and how confident the source was, so
later phases (audit, scoring, AI coaching) never assert something the
user never actually said.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ProfileSource(StrEnum):
    LINKEDIN_API = "linkedin_api"
    PASTE = "paste"
    UPLOAD_PDF = "upload_pdf"
    UPLOAD_DOCX = "upload_docx"
    MANUAL = "manual"
    MERGED = "merged"


class ImportSource(StrEnum):
    """The subset of ProfileSource that goes through the parse-then-review
    pipeline in `profile_imports` (LinkedIn sync and the manual form commit
    directly — see app/profiles/service.py)."""

    PASTE = "paste"
    UPLOAD_PDF = "upload_pdf"
    UPLOAD_DOCX = "upload_docx"


class ImportStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    NEEDS_REVIEW = "needs_review"
    COMMITTED = "committed"
    FAILED = "failed"


class LinkedInSyncStatus(StrEnum):
    NEVER_SYNCED = "never_synced"
    SYNCING = "syncing"
    OK = "ok"
    ERROR = "error"


class SnapshotBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatePart(SnapshotBaseModel):
    """A partial date as LinkedIn and resumes actually give it to us."""

    year: int | None = None
    month: int | None = Field(default=None, ge=1, le=12)


class Identity(SnapshotBaseModel):
    full_name: str | None = None
    headline: str | None = None
    custom_url: str | None = None
    industry: str | None = None
    location: str | None = None
    profile_picture_url: str | None = None


class Experience(SnapshotBaseModel):
    company: str | None = None
    title: str | None = None
    employment_type: str | None = None
    location: str | None = None
    start: DatePart | None = None
    end: DatePart | None = None
    is_current: bool | None = None
    description: str | None = None
    bullets: list[str] | None = None
    skills: list[str] | None = None


class Education(SnapshotBaseModel):
    school: str | None = None
    degree: str | None = None
    field: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    description: str | None = None


class Skill(SnapshotBaseModel):
    name: str | None = None
    endorsements: int | None = None
    is_top: bool | None = None


class Certification(SnapshotBaseModel):
    name: str | None = None
    issuer: str | None = None
    issued: DatePart | None = None
    credential_id: str | None = None
    url: str | None = None


class Language(SnapshotBaseModel):
    name: str | None = None
    proficiency: str | None = None


class Project(SnapshotBaseModel):
    name: str | None = None
    description: str | None = None
    url: str | None = None
    start: DatePart | None = None
    end: DatePart | None = None


class Metrics(SnapshotBaseModel):
    connections: int | None = None
    followers: int | None = None
    recommendations_received: int | None = None


class FieldProvenance(SnapshotBaseModel):
    source: ProfileSource
    confidence: float = Field(ge=0.0, le=1.0)


class ProfileSnapshot(SnapshotBaseModel):
    """The one canonical shape every input path must converge on."""

    version: int = 1
    source: ProfileSource
    captured_at: datetime

    identity: Identity | None = None
    about: str | None = None
    experiences: list[Experience] | None = None
    education: list[Education] | None = None
    skills: list[Skill] | None = None
    certifications: list[Certification] | None = None
    languages: list[Language] | None = None
    projects: list[Project] | None = None
    metrics: Metrics | None = None

    # Keyed by a JSON-pointer-shaped path, e.g. "/identity/headline" or
    # "/experiences/0/title" — a plain str key rather than a real
    # RFC 6901 pointer type, since we only ever build and read these
    # ourselves and never need pointer arithmetic.
    field_provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
