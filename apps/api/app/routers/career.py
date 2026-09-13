"""The Career Hub's resume/job-description HTTP surface. See
app/career/service.py and app/career/parse.py for the domain logic --
this is a thin translation layer, same discipline as app/routers/tools.py.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.career import service
from app.career.export import export_resume_docx, export_resume_pdf
from app.career.parse import parse_resume_paste, parse_resume_upload
from app.career.schema import JobDescriptionSource, ResumeDocument, ResumeSource
from app.content.asset_service import create_asset
from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.resume_match import ResumeMatch
from app.models.user import User
from app.profiles.parsers.documents import UnsupportedDocumentError
from app.profiles.schema import ProfileSnapshot
from app.profiles.service import get_active_snapshot
from app.schemas.career import (
    CommitResumeRequest,
    CreateResumeMatchRequest,
    JobDescriptionParseRequest,
    JobDescriptionResponse,
    ResumeMatchResponse,
    ResumeParseResponse,
    ResumeResponse,
)
from app.settings import settings
from app.tools.definition import AssetType

router = APIRouter(prefix="/api/v1/career", tags=["career"])


def _to_resume_response(resume: Resume) -> ResumeResponse:
    return ResumeResponse(
        id=str(resume.id),
        title=resume.title,
        source=resume.source,
        parsed=ResumeDocument.model_validate(resume.parsed),
        version=resume.version,
        is_active=resume.is_active,
        ats_score=resume.ats_score,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


def _to_job_description_response(job_description: JobDescription) -> JobDescriptionResponse:
    return JobDescriptionResponse(
        id=str(job_description.id),
        title=job_description.title,
        company=job_description.company,
        source=job_description.source,
        raw_text=job_description.raw_text,
        parsed=job_description.parsed,
        created_at=job_description.created_at,
        updated_at=job_description.updated_at,
    )


def _to_match_response(match: ResumeMatch) -> ResumeMatchResponse:
    return ResumeMatchResponse(
        id=str(match.id),
        resume_id=str(match.resume_id),
        job_description_id=str(match.job_description_id),
        overall_match=match.overall_match,
        component_scores=match.component_scores,
        matched=match.matched,
        missing=match.missing,
        transferable=match.transferable,
        created_at=match.created_at,
    )


@router.post("/resumes/parse/paste", response_model=ResumeParseResponse)
async def parse_resume_paste_endpoint(
    payload: dict[str, str],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeParseResponse:
    text = payload.get("text", "")
    if not text.strip():
        raise ApiError(ErrorCode.VALIDATION_FAILED, "Pasted resume text is empty.")
    draft, warnings = await parse_resume_paste(text, user=user, db=db)
    return ResumeParseResponse(draft=draft, warnings=warnings)


@router.post("/resumes/parse/upload", response_model=ResumeParseResponse)
async def parse_resume_upload_endpoint(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeParseResponse:
    content = await file.read()
    if len(content) > settings.profile_upload_max_bytes:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED,
            f"File is too large (max {settings.profile_upload_max_bytes} bytes).",
        )
    try:
        draft, warnings = await parse_resume_upload(
            content, file.content_type or "", user=user, db=db
        )
    except UnsupportedDocumentError as exc:
        raise ApiError(ErrorCode.VALIDATION_FAILED, str(exc)) from exc
    return ResumeParseResponse(draft=draft, warnings=warnings)


@router.post("/resumes/from-profile", response_model=ResumeParseResponse)
async def parse_resume_from_profile_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeParseResponse:
    snapshot_row = await get_active_snapshot(db, user_id=user.id)
    if snapshot_row is None:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED,
            "No profile snapshot to import from yet -- connect LinkedIn or build your "
            "profile first.",
        )
    snapshot = ProfileSnapshot.model_validate(snapshot_row.payload)
    draft = service.build_resume_document_from_profile_snapshot(snapshot)
    return ResumeParseResponse(draft=draft, warnings=[])


@router.post("/resumes", response_model=ResumeResponse)
async def commit_resume_endpoint(
    payload: CommitResumeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    try:
        source = ResumeSource(payload.source)
    except ValueError as exc:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED, f"invalid resume source {payload.source!r}"
        ) from exc
    original_file_ref = uuid.UUID(payload.original_file_ref) if payload.original_file_ref else None
    resume = await service.commit_resume(
        db,
        user=user,
        title=payload.title,
        source=source,
        document=payload.document,
        original_file_ref=original_file_ref,
    )
    return _to_resume_response(resume)


@router.get("/resumes", response_model=list[ResumeResponse])
async def list_resumes_endpoint(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ResumeResponse]:
    resumes = await service.list_resumes(db, user_id=user.id)
    return [_to_resume_response(resume) for resume in resumes]


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume_endpoint(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    resume = await service.get_resume_for_user(db, resume_id=resume_id, user_id=user.id)
    return _to_resume_response(resume)


@router.post("/resumes/{resume_id}/activate", response_model=ResumeResponse)
async def activate_resume_endpoint(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    resume = await service.activate_resume(db, user=user, resume_id=resume_id)
    return _to_resume_response(resume)


@router.delete("/resumes/{resume_id}", status_code=204)
async def delete_resume_endpoint(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.delete_resume(db, user=user, resume_id=resume_id)


@router.post("/resumes/{resume_id}/export/pdf")
async def export_resume_pdf_endpoint(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    resume = await service.get_resume_for_user(db, resume_id=resume_id, user_id=user.id)
    document = ResumeDocument.model_validate(resume.parsed)
    pdf_bytes = export_resume_pdf(document)
    await create_asset(
        db,
        user=user,
        type=AssetType.RESUME,
        title=resume.title,
        body=json.dumps(resume.parsed),
        body_format="json",
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{resume.title}.pdf"'},
    )


@router.post("/resumes/{resume_id}/export/docx")
async def export_resume_docx_endpoint(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    resume = await service.get_resume_for_user(db, resume_id=resume_id, user_id=user.id)
    document = ResumeDocument.model_validate(resume.parsed)
    docx_bytes = export_resume_docx(document)
    await create_asset(
        db,
        user=user,
        type=AssetType.RESUME,
        title=resume.title,
        body=json.dumps(resume.parsed),
        body_format="json",
    )
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{resume.title}.docx"'},
    )


@router.post("/job-descriptions", response_model=JobDescriptionResponse)
async def create_job_description_endpoint(
    payload: JobDescriptionParseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobDescriptionResponse:
    if not payload.raw_text.strip():
        raise ApiError(ErrorCode.VALIDATION_FAILED, "Job description text is empty.")
    job_description = await service.commit_job_description(
        db,
        user=user,
        title=payload.title,
        company=payload.company,
        source=JobDescriptionSource.PASTE,
        raw_text=payload.raw_text,
    )
    return _to_job_description_response(job_description)


@router.get("/job-descriptions", response_model=list[JobDescriptionResponse])
async def list_job_descriptions_endpoint(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[JobDescriptionResponse]:
    job_descriptions = await service.list_job_descriptions(db, user_id=user.id)
    return [_to_job_description_response(jd) for jd in job_descriptions]


@router.get("/job-descriptions/{job_description_id}", response_model=JobDescriptionResponse)
async def get_job_description_endpoint(
    job_description_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobDescriptionResponse:
    job_description = await service.get_job_description_for_user(
        db, job_description_id=job_description_id, user_id=user.id
    )
    return _to_job_description_response(job_description)


@router.delete("/job-descriptions/{job_description_id}", status_code=204)
async def delete_job_description_endpoint(
    job_description_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.delete_job_description(db, user=user, job_description_id=job_description_id)


@router.post("/matches", response_model=ResumeMatchResponse)
async def create_match_endpoint(
    payload: CreateResumeMatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeMatchResponse:
    match = await service.create_resume_match(
        db,
        user=user,
        resume_id=uuid.UUID(payload.resume_id),
        job_description_id=uuid.UUID(payload.job_description_id),
    )
    return _to_match_response(match)


@router.get("/matches", response_model=list[ResumeMatchResponse])
async def list_matches_endpoint(
    resume_id: uuid.UUID | None = Query(default=None),
    job_description_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResumeMatchResponse]:
    matches = await service.list_resume_matches(
        db, user_id=user.id, resume_id=resume_id, job_description_id=job_description_id
    )
    return [_to_match_response(match) for match in matches]
