"""Voice profile derivation: turns the user's own past posts into a
descriptor every content tool's prompt can read via
`ContextKey.VOICE_PROFILE`. Never a scrape -- the user pastes or
uploads their own text (CLAUDE.md's parity-path rule: this works
identically for a user who never connects LinkedIn).

Reading the active descriptor is a pure query: a user who has never
submitted samples gets a neutral, hardcoded default descriptor handed
back in memory, never persisted as if it were learned -- so `assemble()`
(which calls this indirectly through `app/tools/context.py`) stays a
read-only path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.content.style_signals import compute_style_signals
from app.errors import ApiError, ErrorCode
from app.models.content_sample import ContentSample
from app.models.user import User
from app.models.voice_profile import VoiceProfile

MIN_SAMPLES = 5
MAX_SAMPLES = 20

DEFAULT_DESCRIPTOR: dict[str, Any] = {
    "tone_adjectives": ["clear", "professional", "direct"],
    "recurring_themes": [],
    "signature_structures": [],
    "vocabulary_preferences": [],
    "never_does": ["slang", "excessive hype language"],
}


class InvalidSampleCount(ApiError):
    def __init__(self, count: int) -> None:
        super().__init__(
            ErrorCode.VALIDATION_FAILED,
            f"Provide between {MIN_SAMPLES} and {MAX_SAMPLES} posts (got {count}).",
        )


@dataclass(frozen=True, slots=True)
class VoiceDescriptor:
    source: Literal["supplied", "derived", "default"]
    sample_count: int
    descriptor: dict[str, Any]


async def get_active_descriptor(db: AsyncSession, *, user: User) -> VoiceDescriptor:
    row = (
        await db.execute(
            select(VoiceProfile).where(
                VoiceProfile.user_id == user.id, VoiceProfile.is_active.is_(True)
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return VoiceDescriptor(source="default", sample_count=0, descriptor=DEFAULT_DESCRIPTOR)
    return VoiceDescriptor(
        source=row.source,  # type: ignore[arg-type]
        sample_count=row.sample_count,
        descriptor=row.descriptor,
    )


async def submit_voice_samples(
    db: AsyncSession, *, user: User, texts: list[str], source: str
) -> VoiceProfile:
    if not MIN_SAMPLES <= len(texts) <= MAX_SAMPLES:
        raise InvalidSampleCount(len(texts))

    for text in texts:
        db.add(ContentSample(user_id=user.id, body=text, source=source))

    signals = compute_style_signals(texts)
    context = {
        "style_signals": signals.to_context_block(),
        "samples": "\n\n---\n\n".join(texts),
    }
    result = await gateway.run("content.voice_profile.v1", context, user=user, db=db)
    assert result.parsed is not None  # the prompt declares a JSON output_schema

    await db.execute(
        update(VoiceProfile)
        .where(VoiceProfile.user_id == user.id, VoiceProfile.is_active.is_(True))
        .values(is_active=False)
    )
    profile = VoiceProfile(
        user_id=user.id,
        source="derived",
        sample_count=len(texts),
        descriptor=result.parsed,
        is_active=True,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile
