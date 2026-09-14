"""The Dashboard's single aggregate read -- one round trip for everything
above the fold (FRD §11): health score, trend, top recommendations, hub
tiles, and the run-audit control's state. Never gated behind the "audit"
feature flag itself, since the Dashboard is a top-level surface every
user lands on (CLAUDE.md's product vocabulary) -- `hubs` tells the web
app which sections to show.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.presenters import to_category_result_response, to_recommendation_response
from app.audit.service import DASHBOARD_SCORE_HISTORY_DAYS, get_dashboard_snapshot
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.audit import ScoreHistoryPoint
from app.schemas.dashboard import (
    DashboardHealthScore,
    DashboardResponse,
    DashboardRunAuditState,
    DashboardScoreHistory,
    DashboardUser,
)
from app.services.feature_flags import resolve_flags_for_user

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    snapshot = await get_dashboard_snapshot(db, user=user)
    hubs = await resolve_flags_for_user(db, user_id=user.id)

    health_score: DashboardHealthScore | None = None
    if snapshot.latest_audit is not None:
        audit = snapshot.latest_audit
        health_score = DashboardHealthScore(
            audit_id=str(audit.id),
            overall=audit.overall_score,
            scoring_version=audit.scoring_version,
            status=audit.status,
            completed_at=audit.completed_at,
            categories=[
                to_category_result_response(
                    result, snapshot.top_findings_by_category.get(result.category, [])
                )
                for result in snapshot.category_results
            ],
        )

    points = [
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
        for row in snapshot.score_history
    ]
    delta = points[-1].overall - points[0].overall if len(points) >= 2 else None

    return DashboardResponse(
        user=DashboardUser(full_name=user.full_name, plan=user.plan),
        is_first_time=snapshot.latest_audit is None,
        health_score=health_score,
        score_history=DashboardScoreHistory(
            range=f"{DASHBOARD_SCORE_HISTORY_DAYS}d", points=points, delta=delta
        ),
        top_recommendations=[
            to_recommendation_response(rec) for rec in snapshot.top_recommendations
        ],
        run_audit=DashboardRunAuditState(
            can_run=snapshot.run_audit.can_run,
            reason=snapshot.run_audit.reason,  # type: ignore[arg-type]
            retry_after_seconds=snapshot.run_audit.retry_after_seconds,
            in_flight_job_id=(
                str(snapshot.run_audit.in_flight_job_id)
                if snapshot.run_audit.in_flight_job_id
                else None
            ),
            quota_used=snapshot.run_audit.quota.used,
            quota_limit=snapshot.run_audit.quota.limit,
        ),
        hubs=hubs,
    )
