"""The resume/job-description data layer: commit a reviewed draft,
list and fetch, manage `is_active`, and run+persist a resume<->JD
match. Parsing itself (app.career.parse, app.career.parsers.*) never
writes to the database -- everything here is the write path a draft
converges on once the user has reviewed and corrected it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.career.parsers.job_description import parse_job_description
from app.career.schema import (
    JobDescriptionSource,
    ResumeContact,
    ResumeDocument,
    ResumeEducation,
    ResumeExperience,
    ResumeSkills,
    ResumeSource,
)
from app.errors import ApiError, ErrorCode
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.resume_match import ResumeMatch
from app.models.user import User
from app.profiles.schema import ProfileSnapshot
from app.tools import service as tool_service


def build_resume_document_from_profile_snapshot(snapshot: ProfileSnapshot) -> ResumeDocument:
    """Deterministic structural mapping, ProfileSnapshot -> ResumeDocument
    -- no AI involved, since every field here already exists verbatim in
    the snapshot. Used both by the Career Hub's "import from profile"
    action and as Resume Builder's starting draft when building from the
    profile rather than from scratch."""
    contact = None
    if snapshot.identity is not None:
        contact = ResumeContact(
            full_name=snapshot.identity.full_name, location=snapshot.identity.location
        )

    experiences = [
        ResumeExperience(
            company=exp.company,
            title=exp.title,
            location=exp.location,
            start=exp.start,
            end=exp.end,
            is_current=exp.is_current,
            bullets=list(exp.bullets or []),
        )
        for exp in (snapshot.experiences or [])
    ]
    education = [
        ResumeEducation(
            school=edu.school,
            degree=edu.degree,
            field=edu.field,
            description=edu.description,
        )
        for edu in (snapshot.education or [])
    ]
    skills = ResumeSkills(technical=[s.name for s in (snapshot.skills or []) if s.name])

    return ResumeDocument(
        version=1,
        source=ResumeSource.IMPORTED_FROM_PROFILE,
        contact=contact,
        summary=snapshot.about,
        experiences=experiences,
        education=education,
        skills=skills,
    )


async def _next_resume_version(db: AsyncSession, *, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(Resume.version)
        .where(Resume.user_id == user_id)
        .order_by(Resume.version.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    return (latest or 0) + 1


async def commit_resume(
    db: AsyncSession,
    *,
    user: User,
    title: str,
    source: ResumeSource,
    document: ResumeDocument,
    original_file_ref: uuid.UUID | None = None,
) -> Resume:
    """Persists a reviewed (possibly user-corrected) draft as a new,
    active version -- deactivating whatever was previously active, the
    same versioning shape `VoiceProfile` uses."""
    await db.execute(
        update(Resume)
        .where(Resume.user_id == user.id, Resume.is_active.is_(True))
        .values(is_active=False)
    )
    resume = Resume(
        user_id=user.id,
        title=title,
        source=source.value,
        original_file_ref=original_file_ref,
        parsed=document.model_dump(mode="json"),
        version=await _next_resume_version(db, user_id=user.id),
        is_active=True,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


async def get_resume_for_user(
    db: AsyncSession, *, resume_id: uuid.UUID, user_id: uuid.UUID
) -> Resume:
    resume = await db.get(Resume, resume_id)
    if resume is None or resume.user_id != user_id or resume.deleted_at is not None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such resume")
    return resume


async def list_resumes(db: AsyncSession, *, user_id: uuid.UUID) -> list[Resume]:
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user_id, Resume.deleted_at.is_(None))
        .order_by(Resume.created_at.desc())
    )
    return list(result.scalars().all())


async def activate_resume(db: AsyncSession, *, user: User, resume_id: uuid.UUID) -> Resume:
    resume = await get_resume_for_user(db, resume_id=resume_id, user_id=user.id)
    await db.execute(
        update(Resume)
        .where(Resume.user_id == user.id, Resume.is_active.is_(True))
        .values(is_active=False)
    )
    resume.is_active = True
    await db.commit()
    await db.refresh(resume)
    return resume


async def delete_resume(db: AsyncSession, *, user: User, resume_id: uuid.UUID) -> None:
    resume = await get_resume_for_user(db, resume_id=resume_id, user_id=user.id)
    resume.deleted_at = datetime.now(UTC)
    if resume.is_active:
        resume.is_active = False
    await db.commit()


async def commit_job_description(
    db: AsyncSession,
    *,
    user: User,
    title: str,
    company: str | None,
    source: JobDescriptionSource,
    raw_text: str,
) -> JobDescription:
    parsed = parse_job_description(raw_text)
    job_description = JobDescription(
        user_id=user.id,
        title=title,
        company=company,
        source=source.value,
        raw_text=raw_text,
        parsed=parsed.model_dump(mode="json"),
    )
    db.add(job_description)
    await db.commit()
    await db.refresh(job_description)
    return job_description


async def get_job_description_for_user(
    db: AsyncSession, *, job_description_id: uuid.UUID, user_id: uuid.UUID
) -> JobDescription:
    job_description = await db.get(JobDescription, job_description_id)
    if (
        job_description is None
        or job_description.user_id != user_id
        or job_description.deleted_at is not None
    ):
        raise ApiError(ErrorCode.NOT_FOUND, "no such job description")
    return job_description


async def list_job_descriptions(db: AsyncSession, *, user_id: uuid.UUID) -> list[JobDescription]:
    result = await db.execute(
        select(JobDescription)
        .where(JobDescription.user_id == user_id, JobDescription.deleted_at.is_(None))
        .order_by(JobDescription.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_job_description(
    db: AsyncSession, *, user: User, job_description_id: uuid.UUID
) -> None:
    job_description = await get_job_description_for_user(
        db, job_description_id=job_description_id, user_id=user.id
    )
    job_description.deleted_at = datetime.now(UTC)
    await db.commit()


async def create_resume_match(
    db: AsyncSession, *, user: User, resume_id: uuid.UUID, job_description_id: uuid.UUID
) -> ResumeMatch:
    """Runs `career.resume_jd_match` and persists its output as a
    `ResumeMatch` row -- this is Career Hub-specific glue, not a Tool
    Framework concern (see docs/adr/0008), which is why it lives here
    rather than as a generic `postprocess` hook."""
    resume = await get_resume_for_user(db, resume_id=resume_id, user_id=user.id)
    job_description = await get_job_description_for_user(
        db, job_description_id=job_description_id, user_id=user.id
    )

    run, _quota, _warning = await tool_service.run_tool(
        db,
        user=user,
        tool_id="career.resume_jd_match",
        raw_input={
            "resume_text": _resume_document_as_text(resume.parsed),
            "job_description_text": job_description.raw_text,
        },
    )
    output = run.output
    assert output is not None

    match = ResumeMatch(
        user_id=user.id,
        resume_id=resume.id,
        job_description_id=job_description.id,
        overall_match=output["overall_match"],
        component_scores=output["component_scores"],
        matched=output["matched"],
        missing=output["missing"],
        transferable=output["transferable"],
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


async def list_resume_matches(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID | None = None,
    job_description_id: uuid.UUID | None = None,
) -> list[ResumeMatch]:
    stmt = select(ResumeMatch).where(
        ResumeMatch.user_id == user_id, ResumeMatch.deleted_at.is_(None)
    )
    if resume_id is not None:
        stmt = stmt.where(ResumeMatch.resume_id == resume_id)
    if job_description_id is not None:
        stmt = stmt.where(ResumeMatch.job_description_id == job_description_id)
    result = await db.execute(stmt.order_by(ResumeMatch.created_at.desc()))
    return list(result.scalars().all())


def _resume_document_as_text(parsed: dict[str, object]) -> str:
    """A plain-text rendering of a parsed ResumeDocument, for feeding to
    a tool prompt that expects free text rather than the JSON shape --
    every career.* tool that takes "a resume" as input takes it this
    way, mirroring how `career.resume_analyzer` and friends are defined."""
    document = ResumeDocument.model_validate(parsed)
    lines: list[str] = []
    if document.contact and document.contact.full_name:
        lines.append(document.contact.full_name)
    if document.summary:
        lines.append(document.summary)
    for exp in document.experiences:
        header = " ".join(part for part in (exp.title, exp.company) if part)
        if header:
            lines.append(header)
        lines.extend(f"- {bullet}" for bullet in exp.bullets)
    for edu in document.education:
        header = " ".join(part for part in (edu.degree, edu.school) if part)
        if header:
            lines.append(header)
    if document.skills:
        lines.append(", ".join(document.skills.technical + document.skills.tools))
    return "\n".join(lines)
