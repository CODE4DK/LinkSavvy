"""Runs all five category audits for one user, persists the results, and
rolls them up into an overall score.

Categories run concurrently via `asyncio.gather` -- a slow or failing one
never blocks the others. A category that raises or times out is recorded
as `status="failed"` with its weight dropped from the overall score
(renormalized via `weighted_average`), never silently treated as a zero;
the audit as a whole is still marked `completed_with_errors` rather than
`failed` outright, since a partial result is still useful to show.

`role_keywords` is resolved exactly once here, before the categories run,
rather than by each category independently -- see
app/audit/role_keywords.py for why.
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.categories import career, content, engagement, profile, visibility
from app.audit.context import AuditContext
from app.audit.models import Category, CategoryResult
from app.audit.recommendations import build_recommendations
from app.audit.role_keywords import get_role_keywords
from app.audit.scoring import load_scoring_config, weighted_average
from app.audit.target_role import resolve_target_role
from app.db import AsyncSessionLocal, SessionFactory
from app.models.audit import Audit, AuditCategoryResult, AuditFinding
from app.models.profile_snapshot import ProfileSnapshotRow
from app.models.score_history import ScoreHistory
from app.models.user import User
from app.profiles.completeness import compute_completeness
from app.profiles.schema import ProfileSnapshot

logger = logging.getLogger("app.audit.orchestrator")

CATEGORY_TIMEOUT_SECONDS = 30.0


class _CategoryModule(Protocol):
    async def run(self, ctx: AuditContext) -> CategoryResult: ...


_CATEGORY_MODULES: dict[Category, _CategoryModule] = {
    "profile": profile,
    "content": content,
    "engagement": engagement,
    "career": career,
    "visibility": visibility,
}


async def _run_category(
    category: Category, ctx: AuditContext, session_factory: SessionFactory
) -> CategoryResult:
    # Each category gets its own session rather than sharing the caller's:
    # AsyncSession isn't safe to use from more than one coroutine at a
    # time, and these run concurrently via asyncio.gather below. Only
    # `db` changes -- everything else on the context (snapshot,
    # completeness, role_keywords, ...) is shared read-only data.
    module = _CATEGORY_MODULES[category]
    try:
        async with session_factory() as category_db:
            category_ctx = dataclasses.replace(ctx, db=category_db)
            return await asyncio.wait_for(
                module.run(category_ctx), timeout=CATEGORY_TIMEOUT_SECONDS
            )
    except Exception:
        logger.exception(
            "audit_category_failed",
            extra={"category": category, "correlation_id": ctx.correlation_id},
        )
        return CategoryResult(
            category=category,
            status="failed",
            score=None,
            inputs_available={},
            detail={},
            findings=[],
        )


async def run_audit(
    *,
    user: User,
    db: AsyncSession,
    snapshot_row: ProfileSnapshotRow,
    trigger: str,
    target_role: str | None = None,
    content_history: list[str] | None = None,
    session_factory: SessionFactory = AsyncSessionLocal,
) -> Audit:
    started = time.monotonic()
    config = load_scoring_config()
    snapshot = ProfileSnapshot.model_validate(snapshot_row.payload)

    resolved_target_role, target_role_is_assumed = resolve_target_role(
        snapshot, supplied=target_role
    )
    role_keywords = await get_role_keywords(target_role=resolved_target_role, user=user, db=db)
    completeness = compute_completeness(snapshot)

    ctx = AuditContext(
        user=user,
        db=db,
        snapshot=snapshot,
        completeness=completeness,
        correlation_id=str(uuid.uuid4()),
        content_history=content_history,
        target_role=resolved_target_role,
        target_role_is_assumed=target_role_is_assumed,
        role_keywords=role_keywords,
    )

    audit = Audit(
        user_id=user.id,
        profile_snapshot_id=snapshot_row.id,
        status="running",
        scoring_version=config.scoring_version,
        started_at=datetime.now(UTC),
        trigger=trigger,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    results = list(
        await asyncio.gather(
            *(_run_category(category, ctx, session_factory) for category in _CATEGORY_MODULES)
        )
    )

    category_scores: dict[str, int | None] = {}
    any_failed = False
    for result in results:
        category_scores[result.category] = result.score
        if result.status == "failed":
            any_failed = True
        db.add(
            AuditCategoryResult(
                audit_id=audit.id,
                category=result.category,
                score=result.score,
                status=result.status,
                inputs_available=result.inputs_available,
                detail=result.detail,
            )
        )
        for finding in result.findings:
            db.add(
                AuditFinding(
                    audit_id=audit.id,
                    category=result.category,
                    code=finding.code,
                    severity=finding.severity,
                    title=finding.title,
                    evidence=finding.evidence,
                    deterministic=finding.deterministic,
                )
            )

    overall_score = weighted_average(category_scores, config.category_weights)

    audit.status = "completed_with_errors" if any_failed else "completed"
    audit.overall_score = overall_score
    audit.completed_at = datetime.now(UTC)
    audit.duration_ms = round((time.monotonic() - started) * 1000)
    await db.commit()
    await db.refresh(audit)

    if overall_score is not None:
        db.add(
            ScoreHistory(
                user_id=user.id,
                audit_id=audit.id,
                scoring_version=config.scoring_version,
                overall=overall_score,
                profile=category_scores.get("profile"),
                content=category_scores.get("content"),
                engagement=category_scores.get("engagement"),
                career=category_scores.get("career"),
                visibility=category_scores.get("visibility"),
                recorded_at=datetime.now(UTC),
            )
        )

    for recommendation in build_recommendations(
        audit_id=audit.id, user_id=user.id, results=results
    ):
        db.add(recommendation)

    await db.commit()
    return audit
