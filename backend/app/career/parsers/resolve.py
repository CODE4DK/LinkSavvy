"""The one AI gateway call a resume parse is allowed: resolving
whatever `app.career.parsers.segment.segment_resume_text` could not
confidently turn into structured fields on its own. Called at most
once per parse, with every ambiguous segment batched into a single
prompt -- never one call per segment.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.career.parsers.segment import AmbiguousSegment
from app.career.schema import (
    ProvenanceSource,
    ResumeCustomSection,
    ResumeDocument,
    ResumeExperience,
    ResumeFieldProvenance,
)
from app.models.user import User
from app.profiles.schema import DatePart

RESOLVE_PROMPT_ID = "career.resume_segment_resolver.v1"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _ResolvedExperience(_StrictModel):
    segment_id: str
    company: str | None = None
    title: str | None = None
    location: str | None = None
    start: DatePart | None = None
    end: DatePart | None = None
    is_current: bool | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class _ResolvedCustomSection(_StrictModel):
    segment_id: str
    heading: str
    bullets: list[str] = Field(default_factory=list)


class ResolveOutput(_StrictModel):
    experiences: list[_ResolvedExperience] = Field(default_factory=list)
    custom_sections: list[_ResolvedCustomSection] = Field(default_factory=list)


def _render_segments(segments: list[AmbiguousSegment]) -> str:
    blocks = []
    for segment in segments:
        blocks.append(
            f"[segment_id: {segment.segment_id}]\n"
            f"(heading guess: {segment.heading_guess})\n"
            f"{segment.raw_text}"
        )
    return "\n\n".join(blocks)


async def resolve_ambiguous_segments(
    document: ResumeDocument,
    segments: list[AmbiguousSegment],
    *,
    user: User,
    db: AsyncSession,
) -> ResumeDocument:
    """Merges the AI's classification of every ambiguous segment into
    `document` and returns it. A no-op (no gateway call at all) when
    there's nothing ambiguous to resolve."""
    if not segments:
        return document

    context = {"segments": _render_segments(segments)}
    result = await gateway.run(RESOLVE_PROMPT_ID, context, user=user, db=db)
    assert result.parsed is not None  # the prompt declares a JSON output_schema
    resolved = ResolveOutput.model_validate(result.parsed)

    ai_resolved = ResumeFieldProvenance(source=ProvenanceSource.AI_RESOLVED, confidence=0.6)

    for item in resolved.experiences:
        document.experiences.append(
            ResumeExperience(
                company=item.company,
                title=item.title,
                location=item.location,
                start=item.start,
                end=item.end,
                is_current=item.is_current,
                bullets=item.bullets,
                technologies=item.technologies,
            )
        )
        document.field_provenance[f"/experiences/{len(document.experiences) - 1}"] = ai_resolved

    for section in resolved.custom_sections:
        document.custom_sections.append(
            ResumeCustomSection(heading=section.heading, bullets=section.bullets)
        )
        document.field_provenance[f"/custom_sections/{len(document.custom_sections) - 1}"] = (
            ai_resolved
        )

    return document
