from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.career.parsers.resolve import resolve_ambiguous_segments
from app.career.parsers.segment import AmbiguousSegment
from app.career.schema import ResumeDocument, ResumeSource
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"resolve-{uuid.uuid4()}@example.com", full_name="Resolve Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_resolve_is_a_no_op_without_ambiguous_segments(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    document = ResumeDocument(version=1, source=ResumeSource.UPLOAD)
    resolved = await resolve_ambiguous_segments(document, [], user=user, db=db_session)
    assert resolved is document
    assert resolved.experiences == []
    assert resolved.custom_sections == []


async def test_resolve_merges_experience_and_custom_sections(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    document = ResumeDocument(version=1, source=ResumeSource.UPLOAD)
    segments = [
        AmbiguousSegment(
            segment_id="experience-0",
            heading_guess="experience",
            raw_text="Freelance Consultant\nHelped several startups design their backend architecture.",
        ),
        AmbiguousSegment(
            segment_id="custom-0",
            heading_guess="VOLUNTEER WORK",
            raw_text="Mentored junior engineers through a local coding bootcamp.",
        ),
    ]

    resolved = await resolve_ambiguous_segments(document, segments, user=user, db=db_session)

    assert len(resolved.experiences) == 1
    assert resolved.experiences[0].title == "Freelance Consultant"
    assert resolved.experiences[0].bullets == [
        "Helped several startups design their backend architecture."
    ]

    assert len(resolved.custom_sections) == 1
    assert resolved.custom_sections[0].heading == "Volunteer Work"

    assert resolved.field_provenance["/experiences/0"].source == "ai_resolved"
    assert resolved.field_provenance["/custom_sections/0"].source == "ai_resolved"


async def test_resolve_never_touches_already_parsed_fields(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    document = ResumeDocument(version=1, source=ResumeSource.UPLOAD, summary="A real summary.")
    segments = [
        AmbiguousSegment(
            segment_id="custom-0", heading_guess="VOLUNTEER WORK", raw_text="Some text."
        )
    ]
    resolved = await resolve_ambiguous_segments(document, segments, user=user, db=db_session)
    assert resolved.summary == "A real summary."
