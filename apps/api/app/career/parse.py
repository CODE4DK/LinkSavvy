"""Top-level entry points for turning raw resume input (an uploaded
file or pasted text) into a reviewable `ResumeDocument` draft. Always
show the result for user correction before committing it -- these
functions only ever produce a draft, never write to `resumes`
themselves (see app/career/service.py for that).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.career.parsers.layout import extract_resume_pdf_text
from app.career.parsers.resolve import resolve_ambiguous_segments
from app.career.parsers.segment import segment_resume_text
from app.career.schema import ResumeDocument, ResumeSource
from app.models.user import User
from app.profiles.parsers.documents import extract_docx_text, sniff_upload_kind


async def parse_resume_upload(
    data: bytes, content_type: str, *, user: User, db: AsyncSession
) -> tuple[ResumeDocument, list[str]]:
    """Returns (draft, warnings). Raises `UnsupportedDocumentError` (see
    app.profiles.parsers.documents) for a file that can't be read."""
    kind = sniff_upload_kind(data, content_type)
    text = extract_resume_pdf_text(data) if kind == "pdf" else extract_docx_text(data)
    result = segment_resume_text(text, source=ResumeSource.UPLOAD)
    document = await resolve_ambiguous_segments(
        result.document, result.ambiguous_segments, user=user, db=db
    )
    return document, result.warnings


async def parse_resume_paste(
    text: str, *, user: User, db: AsyncSession
) -> tuple[ResumeDocument, list[str]]:
    result = segment_resume_text(text, source=ResumeSource.UPLOAD)
    document = await resolve_ambiguous_segments(
        result.document, result.ambiguous_segments, user=user, db=db
    )
    return document, result.warnings
