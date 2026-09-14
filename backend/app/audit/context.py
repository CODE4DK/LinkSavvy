"""Everything a category audit needs, assembled once by the orchestrator
so no category has to know how to fetch its own inputs or call the
gateway directly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.ai.providers.base import ModelTier
from app.models.user import User
from app.profiles.completeness import CompletenessResult
from app.profiles.schema import ProfileSnapshot


@dataclass(frozen=True, slots=True)
class RoleKeywords:
    """The target role's expected vocabulary -- role-generic, not
    profile-specific, so the orchestrator resolves this once per audit
    run (not once per category) and the gateway caches it hard across
    users targeting the same role. See app/audit/role_keywords.py."""

    keywords: list[str]
    must_have_skills: list[str]


@dataclass(frozen=True, slots=True)
class AuditContext:
    user: User
    db: AsyncSession
    snapshot: ProfileSnapshot
    completeness: CompletenessResult
    correlation_id: str
    # None when the user has supplied no post history to assess -- there's
    # no ingestion path for this yet (a later phase's Content Hub feature),
    # so this is realistically always None today; content.py skips
    # gracefully rather than guessing.
    content_history: list[str] | None
    # Either the caller's own input, or inferred from the current
    # experience's title -- target_role_is_assumed tells a category (and
    # its findings' evidence) which one it got.
    target_role: str | None
    target_role_is_assumed: bool
    # Resolved once by the orchestrator (see app/audit/role_keywords.py) so
    # the up-to-four categories that want it don't each trigger their own
    # gateway call for the identical, role-generic answer.
    role_keywords: RoleKeywords | None

    async def run_prompt(
        self,
        prompt_id: str,
        context: dict[str, Any],
        *,
        tier_override: ModelTier | None = None,
    ) -> gateway.GatewayResult:
        return cast(
            gateway.GatewayResult,
            await gateway.run(
                prompt_id, context, user=self.user, db=self.db, tier_override=tier_override
            ),
        )
