from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.content.voice_service import MAX_SAMPLES, MIN_SAMPLES


class VoiceSamplesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texts: list[str] = Field(min_length=MIN_SAMPLES, max_length=MAX_SAMPLES)


class VoiceDescriptorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["supplied", "derived", "default"]
    sample_count: int
    tone_adjectives: list[str]
    recurring_themes: list[str]
    signature_structures: list[str]
    vocabulary_preferences: list[str]
    never_does: list[str]
