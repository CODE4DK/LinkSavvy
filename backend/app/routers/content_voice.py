"""Voice profile capture: paste or upload past posts, derive a
descriptor, and read back whatever descriptor is currently active
(derived, or the neutral default when nothing has been supplied yet).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.voice_service import get_active_descriptor, submit_voice_samples
from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.user import User
from app.profiles.parsers.documents import (
    UnsupportedDocumentError,
    extract_docx_text,
    extract_pdf_text,
    sniff_upload_kind,
)
from app.schemas.content_voice import VoiceDescriptorResponse, VoiceSamplesRequest
from app.settings import settings

router = APIRouter(prefix="/api/v1/content/voice", tags=["content"])

_POST_SEPARATOR = "\n---\n"


def _to_response(descriptor: object, *, source: str, sample_count: int) -> VoiceDescriptorResponse:
    assert isinstance(descriptor, dict)
    return VoiceDescriptorResponse(
        source=source,  # type: ignore[arg-type]
        sample_count=sample_count,
        tone_adjectives=descriptor.get("tone_adjectives", []),
        recurring_themes=descriptor.get("recurring_themes", []),
        signature_structures=descriptor.get("signature_structures", []),
        vocabulary_preferences=descriptor.get("vocabulary_preferences", []),
        never_does=descriptor.get("never_does", []),
    )


@router.get("", response_model=VoiceDescriptorResponse)
async def get_voice_profile(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> VoiceDescriptorResponse:
    voice = await get_active_descriptor(db, user=user)
    return _to_response(voice.descriptor, source=voice.source, sample_count=voice.sample_count)


@router.post("/samples", response_model=VoiceDescriptorResponse)
async def submit_pasted_samples(
    payload: VoiceSamplesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceDescriptorResponse:
    texts = [text.strip() for text in payload.texts if text.strip()]
    profile = await submit_voice_samples(db, user=user, texts=texts, source="paste")
    return _to_response(
        profile.descriptor, source=profile.source, sample_count=profile.sample_count
    )


@router.post("/samples/upload", response_model=VoiceDescriptorResponse)
async def submit_uploaded_samples(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceDescriptorResponse:
    content = await file.read()
    if len(content) > settings.profile_upload_max_bytes:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED,
            f"File is too large (max {settings.profile_upload_max_bytes} bytes).",
        )

    content_type = file.content_type or ""
    try:
        kind = sniff_upload_kind(content, content_type)
        extracted = extract_pdf_text(content) if kind == "pdf" else extract_docx_text(content)
    except UnsupportedDocumentError as exc:
        raise ApiError(ErrorCode.VALIDATION_FAILED, str(exc)) from exc

    texts = [part.strip() for part in extracted.split(_POST_SEPARATOR.strip()) if part.strip()]
    source = "upload_pdf" if kind == "pdf" else "upload_docx"
    profile = await submit_voice_samples(db, user=user, texts=texts, source=source)
    return _to_response(
        profile.descriptor, source=profile.source, sample_count=profile.sample_count
    )
