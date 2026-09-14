"""The Assistant's read-only functions -- safe to call without the
user's confirmation, unlike a tool run. Each one answers a narrow
question from existing data; none of them calls the AI gateway. The
orchestrator calls these directly (there's no live function-calling loop
against a real model here, consistent with how the rest of the codebase
prefers a deterministic-first, AI-only-where-it-adds-value design -- see
docs/adr/0009's weekly recommendation engine for the same shape) and
records what it fetched as a `role="tool"` Message in the conversation
transcript (see docs/adr/0010 for why that's a Message, not an
AIInvocation row -- these aren't gateway calls, so there's no prompt,
tokens, or cost to meter).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import get_latest_audit as _get_latest_audit_row
from app.growth.service import get_growth_scores
from app.models.user import User
from app.profiles.schema import ProfileSnapshot
from app.profiles.service import get_active_snapshot
from app.tools import service as tools_service
from app.tools.definition import Hub
from app.tools.registry import all_tools, get_registry
from app.workspace import assets as workspace_service

_WORKSPACE_SEARCH_LIMIT = 5


async def get_my_profile_summary(db: AsyncSession, *, user: User) -> str:
    row = await get_active_snapshot(db, user_id=user.id)
    if row is None:
        return "No profile has been set up yet."
    snapshot = ProfileSnapshot.model_validate(row.payload)
    identity = snapshot.identity
    parts: list[str] = []
    if identity and identity.full_name:
        parts.append(f"Name: {identity.full_name}.")
    if identity and identity.headline:
        parts.append(f"Headline: {identity.headline}.")
    if snapshot.about:
        parts.append("Has an About section.")
    count = len(snapshot.experiences or [])
    parts.append(f"{count} experience entr{'y' if count == 1 else 'ies'} listed.")
    return " ".join(parts)


async def get_latest_audit(db: AsyncSession, *, user: User) -> str:
    audit = await _get_latest_audit_row(db, user_id=user.id)
    if audit is None:
        return "No audit has been run yet."
    if audit.overall_score is None:
        return (
            f"An audit ran on {audit.created_at.date().isoformat()} but has no overall "
            f"score yet (status: {audit.status})."
        )
    return (
        f"Overall Health Score: {audit.overall_score}/100, from an audit run on "
        f"{audit.created_at.date().isoformat()} (status: {audit.status})."
    )


async def get_my_scores(db: AsyncSession, *, user: User) -> str:
    scores = await get_growth_scores(db, user=user)
    lines = []
    for key, score in scores.items():
        if score.value is None:
            lines.append(f"{key}: {score.status.value} (no value yet)")
        else:
            lines.append(f"{key}: {score.value}/100 ({score.status.value})")
    return "; ".join(lines)


async def search_my_workspace(db: AsyncSession, *, user: User, query: str) -> str:
    page = await workspace_service.list_assets(
        db, user_id=user.id, q=query, limit=_WORKSPACE_SEARCH_LIMIT
    )
    if not page.items:
        return f"No saved items matched {query!r}."
    return "\n".join(f"- [{asset.type}] {asset.title} (id: {asset.id})" for asset in page.items)


async def list_available_tools(db: AsyncSession, *, user: User, hub: str | None = None) -> str:
    definitions = get_registry().by_hub(Hub(hub)) if hub else all_tools()
    definitions = await tools_service.visible_tools(db, user=user, definitions=definitions)
    if not definitions:
        return "(no tools available)"
    return "\n".join(f"- {d.id}: {d.name} -- {d.short_description}" for d in definitions)
