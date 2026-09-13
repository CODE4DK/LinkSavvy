"""The canonical ResumeDocument.

Every resume -- uploaded (PDF/DOCX), built section-by-section, or
imported from a ProfileSnapshot -- is normalised into exactly this
shape before it is stored. Mirrors `app.profiles.schema.ProfileSnapshot`'s
conventions: every field is optional (`None` means "we don't know",
`[]` means "we know there are none"), and `field_provenance` records,
per JSON-pointer-style path, where a value came from and how confident
the parser was -- so a field the parser had to guess at can be shown
to the user for confirmation rather than presented as fact.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.profiles.schema import DatePart


class ResumeSource(StrEnum):
    UPLOAD = "upload"
    BUILT = "built"
    IMPORTED_FROM_PROFILE = "imported_from_profile"


class JobDescriptionSource(StrEnum):
    PASTE = "paste"
    URL_MANUAL = "url_manual"
    UPLOAD = "upload"


class ProvenanceSource(StrEnum):
    """Where one field of a parsed ResumeDocument came from -- distinct
    from `ResumeSource` (which describes the whole document): a single
    upload can still have most fields parsed deterministically and a
    handful resolved by the one-shot AI pass for ambiguous segments."""

    DETERMINISTIC_PARSE = "deterministic_parse"
    AI_RESOLVED = "ai_resolved"
    USER_EDITED = "user_edited"
    BUILT = "built"
    IMPORTED_FROM_PROFILE = "imported_from_profile"


class ResumeBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResumeContact(ResumeBaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    website_url: str | None = None


class ResumeExperience(ResumeBaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    start: DatePart | None = None
    end: DatePart | None = None
    is_current: bool | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class ResumeEducation(ResumeBaseModel):
    school: str | None = None
    degree: str | None = None
    field: str | None = None
    start: DatePart | None = None
    end: DatePart | None = None
    description: str | None = None


class ResumeSkills(ResumeBaseModel):
    technical: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)


class ResumeCertification(ResumeBaseModel):
    name: str | None = None
    issuer: str | None = None
    issued: DatePart | None = None
    credential_id: str | None = None
    url: str | None = None


class ResumeProject(ResumeBaseModel):
    name: str | None = None
    description: str | None = None
    url: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ResumeAward(ResumeBaseModel):
    name: str | None = None
    issuer: str | None = None
    date: DatePart | None = None
    description: str | None = None


class ResumePublication(ResumeBaseModel):
    title: str | None = None
    publisher: str | None = None
    date: DatePart | None = None
    url: str | None = None
    description: str | None = None


class ResumeCustomSection(ResumeBaseModel):
    heading: str
    bullets: list[str] = Field(default_factory=list)


class ResumeFieldProvenance(ResumeBaseModel):
    source: ProvenanceSource
    confidence: float = Field(ge=0.0, le=1.0)


class ResumeDocument(ResumeBaseModel):
    """The one canonical shape every resume input path must converge on."""

    version: int = 1
    source: ResumeSource

    contact: ResumeContact | None = None
    summary: str | None = None
    experiences: list[ResumeExperience] = Field(default_factory=list)
    education: list[ResumeEducation] = Field(default_factory=list)
    skills: ResumeSkills | None = None
    certifications: list[ResumeCertification] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    awards: list[ResumeAward] = Field(default_factory=list)
    publications: list[ResumePublication] = Field(default_factory=list)
    custom_sections: list[ResumeCustomSection] = Field(default_factory=list)

    # Keyed by a JSON-pointer-shaped path, e.g. "/contact/email" or
    # "/experiences/0/title" -- see ProfileSnapshot.field_provenance.
    field_provenance: dict[str, ResumeFieldProvenance] = Field(default_factory=dict)


class JobDescriptionRequirements(ResumeBaseModel):
    """The parsed structure a pasted/uploaded job description reduces
    to -- everything Resume<->JD Match and ATS Optimization score
    against."""

    responsibilities: list[str] = Field(default_factory=list)
    required_qualifications: list[str] = Field(default_factory=list)
    preferred_qualifications: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    seniority: str | None = None
    location: str | None = None
    work_mode: str | None = None
