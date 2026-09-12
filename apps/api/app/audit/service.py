"""Read-side helpers and the manual-run guardrails backing
`app/routers/audits.py` -- ownership checks, the 6-hour manual-run
cooldown, and the `audits` quota reservation all live here so the router
itself stays a thin HTTP translation layer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.quota import QuotaStatus, check_and_reserve, peek
from app.errors import ApiError, ErrorCode
from app.jobs.queue import enqueue
from app.models.audit import Audit, AuditCategoryResult, AuditFinding
from app.models.job import Job
from app.models.recommendation import Recommendation
from app.models.score_history import ScoreHistory
from app.models.user import User
from app.profiles.service import get_active_snapshot

MANUAL_RUN_COOLDOWN = timedelta(hours=6)
_IN_FLIGHT_JOB_STATUSES = ("queued", "leased")
DASHBOARD_SCORE_HISTORY_DAYS = 90
DASHBOARD_TOP_RECOMMENDATIONS = 3
DASHBOARD_TOP_FINDINGS_PER_CATEGORY = 3


async def _find_in_flight_audit_job(db: AsyncSession, *, user_id: uuid.UUID) -> Job | None:
    result = await db.execute(
        select(Job)
        .where(
            Job.user_id == user_id,
            Job.type == "audit",
            Job.status.in_(_IN_FLIGHT_JOB_STATUSES),
        )
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _most_recent_manual_audit(db: AsyncSession, *, user_id: uuid.UUID) -> Audit | None:
    result = await db.execute(
        select(Audit)
        .where(Audit.user_id == user_id, Audit.trigger == "manual")
        .order_by(Audit.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def enqueue_manual_audit(
    db: AsyncSession,
    *,
    user: User,
    target_role: str | None,
    content_history: list[str] | None,
) -> Job:
    """Enforces, in order: an active profile snapshot to audit, no audit
    already in flight, the 6-hour manual cooldown, then the `audits`
    quota -- cheapest and most fundamental checks first, so a request
    that's going to be rejected never reserves quota it didn't need to."""
    if await get_active_snapshot(db, user_id=user.id) is None:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED,
            "Commit a profile snapshot before running an audit.",
        )

    in_flight = await _find_in_flight_audit_job(db, user_id=user.id)
    if in_flight is not None:
        raise ApiError(
            ErrorCode.RATE_LIMITED,
            "An audit is already running. Check its status before starting another.",
            details={"job_id": str(in_flight.id)},
        )

    last_manual = await _most_recent_manual_audit(db, user_id=user.id)
    if last_manual is not None:
        retry_at = last_manual.created_at + MANUAL_RUN_COOLDOWN
        now = datetime.now(UTC)
        if now < retry_at:
            raise ApiError(
                ErrorCode.RATE_LIMITED,
                "You can run another audit once the cooldown period has passed.",
                details={"retry_after_seconds": int((retry_at - now).total_seconds())},
            )

    await check_and_reserve(db, user=user, metric="audits")

    payload: dict[str, object] = {"trigger": "manual"}
    if target_role:
        payload["target_role"] = target_role
    if content_history:
        payload["content_history"] = content_history
    return await enqueue(db, job_type="audit", payload=payload, user_id=user.id)


async def get_audit_for_user(
    db: AsyncSession, *, audit_id: uuid.UUID, user_id: uuid.UUID
) -> Audit | None:
    audit = await db.get(Audit, audit_id)
    if audit is None or audit.user_id != user_id:
        return None
    return audit


async def get_latest_audit(db: AsyncSession, *, user_id: uuid.UUID) -> Audit | None:
    result = await db.execute(
        select(Audit).where(Audit.user_id == user_id).order_by(Audit.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_category_results(
    db: AsyncSession, *, audit_id: uuid.UUID
) -> list[AuditCategoryResult]:
    result = await db.execute(
        select(AuditCategoryResult).where(AuditCategoryResult.audit_id == audit_id)
    )
    return list(result.scalars().all())


async def get_findings_by_category(
    db: AsyncSession, *, audit_id: uuid.UUID
) -> dict[str, list[AuditFinding]]:
    result = await db.execute(select(AuditFinding).where(AuditFinding.audit_id == audit_id))
    by_category: dict[str, list[AuditFinding]] = {}
    for finding in result.scalars().all():
        by_category.setdefault(finding.category, []).append(finding)
    return by_category


async def get_score_history(
    db: AsyncSession, *, user_id: uuid.UUID, since: datetime
) -> list[ScoreHistory]:
    result = await db.execute(
        select(ScoreHistory)
        .where(ScoreHistory.user_id == user_id, ScoreHistory.recorded_at >= since)
        .order_by(ScoreHistory.recorded_at.asc())
    )
    return list(result.scalars().all())


async def list_recommendations(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    status: str | None,
    cursor: int | None,
    limit: int,
) -> list[Recommendation]:
    """Scoped to the user's most recent audit -- a recommendation is a
    snapshot of what that run found, and once a new audit runs, an issue
    that's still present gets a fresh row rather than reviving the old
    one, so showing every past audit's rows here would mean duplicate
    advice for the same issue piling up across runs. `priority` (a dense,
    unique 1..N sequence assigned once per audit by
    app/audit/recommendations.py) is both the display order and the
    cursor key -- no separate id-based cursor needed."""
    latest_audit = await get_latest_audit(db, user_id=user_id)
    if latest_audit is None:
        return []

    stmt = select(Recommendation).where(Recommendation.audit_id == latest_audit.id)
    if status is not None:
        stmt = stmt.where(Recommendation.status == status)
    if cursor is not None:
        stmt = stmt.where(Recommendation.priority > cursor)
    stmt = stmt.order_by(Recommendation.priority.asc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_recommendation_for_user(
    db: AsyncSession, *, recommendation_id: uuid.UUID, user_id: uuid.UUID
) -> Recommendation | None:
    recommendation = await db.get(Recommendation, recommendation_id)
    if recommendation is None or recommendation.user_id != user_id:
        return None
    return recommendation


@dataclass(frozen=True, slots=True)
class DashboardRunAuditState:
    can_run: bool
    # None when can_run is True; otherwise one of "no_active_snapshot",
    # "audit_in_progress", "cooldown_active", "quota_exceeded" -- a closed,
    # display-driving set the web app switches on, not a free-text message.
    reason: str | None
    retry_after_seconds: int | None
    in_flight_job_id: uuid.UUID | None
    quota: QuotaStatus


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    latest_audit: Audit | None
    category_results: list[AuditCategoryResult]
    # Capped per category (DASHBOARD_TOP_FINDINGS_PER_CATEGORY) -- the full
    # list is what GET /api/v1/audits/{id} is for.
    top_findings_by_category: dict[str, list[AuditFinding]]
    score_history: list[ScoreHistory]
    top_recommendations: list[Recommendation]
    run_audit: DashboardRunAuditState


async def get_dashboard_snapshot(db: AsyncSession, *, user: User) -> DashboardSnapshot:
    """Everything the dashboard's single aggregate endpoint needs, in a
    fixed, small number of queries that don't grow with how much history
    or how many findings/recommendations a user has accumulated -- every
    list here is capped with its own LIMIT rather than fetched in full
    and sliced in Python."""
    latest_audit = await get_latest_audit(db, user_id=user.id)

    category_results: list[AuditCategoryResult] = []
    top_findings_by_category: dict[str, list[AuditFinding]] = {}
    top_recommendations: list[Recommendation] = []
    if latest_audit is not None:
        category_results = await get_category_results(db, audit_id=latest_audit.id)
        findings_by_category = await get_findings_by_category(db, audit_id=latest_audit.id)
        top_findings_by_category = {
            category: findings[:DASHBOARD_TOP_FINDINGS_PER_CATEGORY]
            for category, findings in findings_by_category.items()
        }
        recs_result = await db.execute(
            select(Recommendation)
            .where(Recommendation.audit_id == latest_audit.id, Recommendation.status == "open")
            .order_by(Recommendation.priority.asc())
            .limit(DASHBOARD_TOP_RECOMMENDATIONS)
        )
        top_recommendations = list(recs_result.scalars().all())

    since = datetime.now(UTC) - timedelta(days=DASHBOARD_SCORE_HISTORY_DAYS)
    score_history = await get_score_history(db, user_id=user.id, since=since)

    has_snapshot = await get_active_snapshot(db, user_id=user.id) is not None
    in_flight = await _find_in_flight_audit_job(db, user_id=user.id)
    last_manual = await _most_recent_manual_audit(db, user_id=user.id)
    quota = await peek(db, user=user, metric="audits")

    can_run = True
    reason: str | None = None
    retry_after_seconds: int | None = None
    if not has_snapshot:
        can_run, reason = False, "no_active_snapshot"
    elif in_flight is not None:
        can_run, reason = False, "audit_in_progress"
    elif last_manual is not None:
        retry_at = last_manual.created_at + MANUAL_RUN_COOLDOWN
        now = datetime.now(UTC)
        if now < retry_at:
            can_run, reason = False, "cooldown_active"
            retry_after_seconds = int((retry_at - now).total_seconds())
    if can_run and quota.used >= quota.limit:
        can_run, reason = False, "quota_exceeded"

    return DashboardSnapshot(
        latest_audit=latest_audit,
        category_results=category_results,
        top_findings_by_category=top_findings_by_category,
        score_history=score_history,
        top_recommendations=top_recommendations,
        run_audit=DashboardRunAuditState(
            can_run=can_run,
            reason=reason,
            retry_after_seconds=retry_after_seconds,
            in_flight_job_id=in_flight.id if in_flight is not None else None,
            quota=quota,
        ),
    )
