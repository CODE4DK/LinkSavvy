"""Resolves the target role's expected vocabulary, once per audit run.

Called by the orchestrator before it fans out to the five categories --
never by a category directly. Up to four categories (Profile's skills
coverage, Career's role alignment, Visibility's keyword density, and
Content's opportunity seeding) all want the identical, role-generic
answer; resolving it once avoids each of them racing an independent
gateway call for the same not-yet-cached result and quietly quadrupling
the ai_runs cost of a single audit.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import gateway
from app.audit.context import RoleKeywords
from app.models.user import User


async def get_role_keywords(
    *, target_role: str | None, user: User, db: AsyncSession
) -> RoleKeywords | None:
    if not target_role:
        return None
    result = await gateway.run(
        "audit.role_keywords.v1", {"target_role": target_role}, user=user, db=db
    )
    parsed = result.parsed
    return RoleKeywords(keywords=parsed["keywords"], must_have_skills=parsed["must_have_skills"])
