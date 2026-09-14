"""Profile Completeness Checker -- wraps Phase 2's deterministic
`compute_completeness` engine. The score and the list of gaps are never
computed by the AI; `precompute` runs the real engine and hands its
result to the prompt as plain labelled text, so the model's only job is
turning already-known gaps into concrete fix guidance.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.profiles.completeness import compute_completeness
from app.profiles.schema import ProfileSnapshot
from app.profiles.service import get_active_snapshot
from app.tools.context import ContextKey, ContextUnavailable
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    pass


class _Finding(_StrictModel):
    title: str
    severity: Literal["info", "warning", "critical"]
    description: str
    recommendation: str


class _Output(_StrictModel):
    summary: str
    findings: list[_Finding]


async def _precompute(user: User, db: AsyncSession) -> dict[str, str]:
    row = await get_active_snapshot(db, user_id=user.id)
    if row is None:
        raise ContextUnavailable(
            ContextKey.PROFILE_FULL,
            reason="no profile snapshot has been committed yet",
            fix="Complete onboarding, or paste/upload your profile in Profile Hub.",
        )
    snapshot = ProfileSnapshot.model_validate(row.payload)
    result = compute_completeness(snapshot)
    gaps_text = (
        "\n".join(f"- [{gap.severity}] {gap.message} -- {gap.fix_hint}" for gap in result.gaps)
        or "(no gaps -- profile is fully complete)"
    )
    return {
        "completeness_score": f"## Completeness score\n{result.score}/100",
        "completeness_gaps": f"## Gaps found by the completeness engine\n{gaps_text}",
    }


DEFINITION = ToolDefinition(
    id="profile.completeness_checker",
    hub=Hub.PROFILE,
    name="Profile Completeness Checker",
    short_description="Your deterministic completeness score, plus concrete guidance for closing each gap.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.completeness_checker.v1",
    precompute=_precompute,
    result_renderer=ResultRenderer.ANALYSIS,
    save_as=AssetType.ANALYSIS,
)
