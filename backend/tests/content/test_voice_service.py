from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.voice_service import (
    DEFAULT_DESCRIPTOR,
    MAX_SAMPLES,
    MIN_SAMPLES,
    InvalidSampleCount,
    get_active_descriptor,
    submit_voice_samples,
)
from app.models.content_sample import ContentSample
from app.models.user import User
from app.models.voice_profile import VoiceProfile


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"voice-{uuid.uuid4()}@example.com", full_name="Voice Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _sample_texts(count: int) -> list[str]:
    return [f"This is sample post number {i} about my work in engineering." for i in range(count)]


async def test_get_active_descriptor_defaults_when_nothing_submitted(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    voice = await get_active_descriptor(db_session, user=user)
    assert voice.source == "default"
    assert voice.sample_count == 0
    assert voice.descriptor == DEFAULT_DESCRIPTOR

    # A pure read: no row was written for a user who has never submitted.
    row = (
        await db_session.execute(select(VoiceProfile).where(VoiceProfile.user_id == user.id))
    ).scalar_one_or_none()
    assert row is None


@pytest.mark.parametrize("count", [MIN_SAMPLES - 1, MAX_SAMPLES + 1])
async def test_submit_voice_samples_rejects_out_of_range_counts(
    db_session: AsyncSession, count: int
) -> None:
    user = await _create_user(db_session)
    with pytest.raises(InvalidSampleCount):
        await submit_voice_samples(
            db_session, user=user, texts=_sample_texts(max(count, 0)), source="paste"
        )


async def test_submit_voice_samples_derives_and_activates_a_profile(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    texts = _sample_texts(MIN_SAMPLES)

    profile = await submit_voice_samples(db_session, user=user, texts=texts, source="paste")

    assert profile.source == "derived"
    assert profile.sample_count == MIN_SAMPLES
    assert profile.is_active is True
    assert "tone_adjectives" in profile.descriptor

    samples = (
        (await db_session.execute(select(ContentSample).where(ContentSample.user_id == user.id)))
        .scalars()
        .all()
    )
    assert len(samples) == MIN_SAMPLES

    voice = await get_active_descriptor(db_session, user=user)
    assert voice.source == "derived"
    assert voice.sample_count == MIN_SAMPLES


async def test_resubmitting_deactivates_the_previous_profile(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    first = await submit_voice_samples(
        db_session, user=user, texts=_sample_texts(MIN_SAMPLES), source="paste"
    )
    second = await submit_voice_samples(
        db_session, user=user, texts=_sample_texts(MIN_SAMPLES + 1), source="paste"
    )

    await db_session.refresh(first)
    assert first.is_active is False
    assert second.is_active is True

    active_rows = (
        (
            await db_session.execute(
                select(VoiceProfile).where(
                    VoiceProfile.user_id == user.id, VoiceProfile.is_active.is_(True)
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(active_rows) == 1
    assert active_rows[0].id == second.id
