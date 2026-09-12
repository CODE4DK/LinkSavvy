"""The Audit Engine's public API: triggering a run, reading its results,
the 90-day score trend, and the recommendations it produced. See
app/audit/ for the orchestrator and category audits themselves.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import (
    enqueue_manual_audit,
    get_audit_for_user,
    get_category_results,
    get_findings_by_category,
    get_latest_audit,
    get_recommendation_for_user,
    get_score_history,
    list_recommendations,
)
from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.audit import Audit
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.audit import (
    AuditCategoryResultResponse,
    AuditDetailResponse,
    AuditFindingResponse,
    AuditRunRequest,
    AuditRunResponse,
    RecommendationListResponse,
    RecommendationResponse,
    RecommendationUpdateRequest,
    ScoreHistoryPoint,
    ScoreHistoryResponse,
)
from app.services.feature_flags import resolve_flags_for_user

DEFAULT_SCORE_HISTORY_RANGE_DAYS = 90
_RANGE_PATTERN = re.compile(r"^(\d+)d$")


async def require_audit_enabled(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> User:
    flags = await resolve_flags_for_user(db, user_id=user.id)
    if not flags.get("audit", False):
        raise ApiError(ErrorCode.FORBIDDEN, "The Audit Engine is not enabled for this account.")
    return user


def _parse_range_days(range_param: str) -> int:
    match = _RANGE_PATTERN.match(range_param)
    if not match:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "range must look like '90d' (a number of days)")
    return int(match.group(1))


async def _to_detail_response(db: AsyncSession, audit: Audit) -> AuditDetailResponse:
    category_results = await get_category_results(db, audit_id=audit.id)
    findings_by_category = await get_findings_by_category(db, audit_id=audit.id)
    categories = [
        AuditCategoryResultResponse(
            category=result.category,
            score=result.score,
            status=result.status,
            inputs_available=result.inputs_available,
            detail=result.detail,
            findings=[
                AuditFindingResponse(
                    id=str(finding.id),
                    category=finding.category,
                    code=finding.code,
                    severity=finding.severity,
                    title=finding.title,
                    evidence=finding.evidence,
                    deterministic=finding.deterministic,
                )
                for finding in findings_by_category.get(result.category, [])
            ],
        )
        for result in category_results
    ]
    return AuditDetailResponse(
        id=str(audit.id),
        status=audit.status,
        scoring_version=audit.scoring_version,
        overall_score=audit.overall_score,
        trigger=audit.trigger,
        started_at=audit.started_at,
        completed_at=audit.completed_at,
        duration_ms=audit.duration_ms,
        error=audit.error,
        categories=categories,
    )


def _to_recommendation_response(recommendation: Recommendation) -> RecommendationResponse:
    return RecommendationResponse(
        id=str(recommendation.id),
        audit_id=str(recommendation.audit_id),
        category=recommendation.category,
        priority=recommendation.priority,
        title=recommendation.title,
        why=recommendation.why,
        action_label=recommendation.action_label,
        action_route=recommendation.action_route,
        action_tool_id=recommendation.action_tool_id,
        estimated_impact_points=recommendation.estimated_impact_points,
        status=recommendation.status,
        completed_at=recommendation.completed_at,
    )


audits_router = APIRouter(prefix="/api/v1/audits", tags=["audits"])
scores_router = APIRouter(prefix="/api/v1/scores", tags=["audits"])
recommendations_router = APIRouter(prefix="/api/v1/recommendations", tags=["audits"])


@audits_router.post("", response_model=AuditRunResponse, status_code=202)
async def start_audit(
    payload: AuditRunRequest,
    user: User = Depends(require_audit_enabled),
    db: AsyncSession = Depends(get_db),
) -> AuditRunResponse:
    job = await enqueue_manual_audit(
        db,
        user=user,
        target_role=payload.target_role,
        content_history=payload.content_history,
    )
    return AuditRunResponse(job_id=str(job.id))


@audits_router.get("/latest", response_model=AuditDetailResponse)
async def get_latest(
    user: User = Depends(require_audit_enabled),
    db: AsyncSession = Depends(get_db),
) -> AuditDetailResponse:
    audit = await get_latest_audit(db, user_id=user.id)
    if audit is None:
        raise ApiError(ErrorCode.NOT_FOUND, "No audits have been run yet.")
    return await _to_detail_response(db, audit)


@audits_router.get("/{audit_id}", response_model=AuditDetailResponse)
async def get_audit(
    audit_id: uuid.UUID,
    user: User = Depends(require_audit_enabled),
    db: AsyncSession = Depends(get_db),
) -> AuditDetailResponse:
    audit = await get_audit_for_user(db, audit_id=audit_id, user_id=user.id)
    if audit is None:
        raise ApiError(ErrorCode.NOT_FOUND, "No such audit.")
    return await _to_detail_response(db, audit)


@scores_router.get("/history", response_model=ScoreHistoryResponse)
async def get_score_history_endpoint(
    range: str = Query(default=f"{DEFAULT_SCORE_HISTORY_RANGE_DAYS}d"),
    user: User = Depends(require_audit_enabled),
    db: AsyncSession = Depends(get_db),
) -> ScoreHistoryResponse:
    days = _parse_range_days(range)
    since = datetime.now(UTC) - timedelta(days=days)
    rows = await get_score_history(db, user_id=user.id, since=since)
    return ScoreHistoryResponse(
        range=range,
        points=[
            ScoreHistoryPoint(
                audit_id=str(row.audit_id),
                recorded_at=row.recorded_at,
                overall=row.overall,
                profile=row.profile,
                content=row.content,
                engagement=row.engagement,
                career=row.career,
                visibility=row.visibility,
            )
            for row in rows
        ],
    )


@recommendations_router.get("", response_model=RecommendationListResponse)
async def get_recommendations(
    status: str | None = Query(default=None),
    cursor: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_audit_enabled),
    db: AsyncSession = Depends(get_db),
) -> RecommendationListResponse:
    rows = await list_recommendations(
        db, user_id=user.id, status=status, cursor=cursor, limit=limit
    )
    next_cursor = str(rows[-1].priority) if len(rows) == limit else None
    return RecommendationListResponse(
        items=[_to_recommendation_response(row) for row in rows],
        next_cursor=next_cursor,
    )


@recommendations_router.patch("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: uuid.UUID,
    payload: RecommendationUpdateRequest,
    user: User = Depends(require_audit_enabled),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    recommendation = await get_recommendation_for_user(
        db, recommendation_id=recommendation_id, user_id=user.id
    )
    if recommendation is None:
        raise ApiError(ErrorCode.NOT_FOUND, "No such recommendation.")

    recommendation.status = payload.status
    recommendation.completed_at = datetime.now(UTC) if payload.status == "done" else None
    await db.commit()
    await db.refresh(recommendation)
    return _to_recommendation_response(recommendation)
