"""Internal, admin-only observability endpoints. Never proxied to the
public frontend — this is what an operator or the Phase 07 dashboard
queries directly."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.metrics import compute_metrics
from app.deps import get_current_admin, get_db
from app.models.user import User
from app.schemas.internal import GatewayMetricsResponse

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/metrics", response_model=GatewayMetricsResponse)
async def get_gateway_metrics(
    window_hours: int = Query(default=24, ge=1, le=24 * 30),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GatewayMetricsResponse:
    metrics = await compute_metrics(db, window_hours=window_hours)
    return GatewayMetricsResponse(**asdict(metrics))
