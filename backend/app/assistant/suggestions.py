"""Suggested prompts for an empty conversation -- generated from the
user's own open recommendations (app.audit.recommendations' existing
ranked table, the same one the Dashboard and the weekly plan draw from;
see docs/adr/0009's weekly recommendation engine for the same reuse
pattern) rather than a fixed list of generic examples. A user with no
audit yet gets a small, honest set of starter prompts instead -- never a
recommendation-shaped sentence with nothing real behind it.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import list_recommendations
from app.models.user import User

_SUGGESTION_LIMIT = 4

_FALLBACK_PROMPTS = [
    "Run my first audit so you have something to work from",
    "Help me write a headline that stands out",
    "What should I focus on first to grow my LinkedIn presence?",
    "Draft a post about something I'm working on",
]


async def suggested_prompts(db: AsyncSession, *, user: User) -> list[str]:
    recommendations = await list_recommendations(
        db, user_id=user.id, status="open", cursor=None, limit=_SUGGESTION_LIMIT
    )
    if not recommendations:
        return _FALLBACK_PROMPTS
    return [recommendation.action_label for recommendation in recommendations]
