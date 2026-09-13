"""The content calendar's HTTP surface. See
app/content/calendar_service.py for the domain logic.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.content import calendar_service
from app.deps import get_current_user, get_db
from app.models.content_plan import ContentPlan
from app.models.user import User
from app.schemas.content_plans import (
    BulkScheduleRequest,
    ConsistencyWeek,
    ContentPlanCreate,
    ContentPlanResponse,
    ContentPlanUpdate,
    MarkContentPlanPostedRequest,
    RecurringSlotsRequest,
    ReminderRequest,
    RescheduleRequest,
)

router = APIRouter(prefix="/api/v1/content-plans", tags=["content"])


def _to_response(plan: ContentPlan) -> ContentPlanResponse:
    return ContentPlanResponse(
        id=str(plan.id),
        asset_id=str(plan.asset_id) if plan.asset_id else None,
        title=plan.title,
        body_preview=plan.body_preview,
        content_type=plan.content_type,
        status=plan.status,  # type: ignore[arg-type]
        planned_for=plan.planned_for,
        planned_time=plan.planned_time,
        posted_at=plan.posted_at,
        reminder_at=plan.reminder_at,
        recurrence_rule=plan.recurrence_rule,
        tags=plan.tags,
        performance=plan.performance,
        notes=plan.notes,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post("", response_model=ContentPlanResponse)
async def create_plan_endpoint(
    payload: ContentPlanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPlanResponse:
    plan = await calendar_service.create_plan(db, user=user, payload=payload)
    return _to_response(plan)


@router.get("", response_model=list[ContentPlanResponse])
async def list_plans_endpoint(
    start: date = Query(...),
    end: date = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentPlanResponse]:
    plans = await calendar_service.list_plans(db, user=user, start=start, end=end)
    return [_to_response(plan) for plan in plans]


@router.get("/consistency", response_model=list[ConsistencyWeek])
async def consistency_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConsistencyWeek]:
    weeks = await calendar_service.consistency_strip(db, user=user)
    return [
        ConsistencyWeek(week_start=week_start, posted_count=count) for week_start, count in weeks
    ]


@router.get("/{plan_id}", response_model=ContentPlanResponse)
async def get_plan_endpoint(
    plan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPlanResponse:
    plan = await calendar_service.get_owned_plan(db, user=user, plan_id=plan_id)
    return _to_response(plan)


@router.patch("/{plan_id}", response_model=ContentPlanResponse)
async def update_plan_endpoint(
    plan_id: uuid.UUID,
    payload: ContentPlanUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPlanResponse:
    plan = await calendar_service.update_plan(db, user=user, plan_id=plan_id, payload=payload)
    return _to_response(plan)


@router.post("/{plan_id}/reschedule", response_model=ContentPlanResponse)
async def reschedule_plan_endpoint(
    plan_id: uuid.UUID,
    payload: RescheduleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPlanResponse:
    plan = await calendar_service.reschedule_plan(db, user=user, plan_id=plan_id, payload=payload)
    return _to_response(plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan_endpoint(
    plan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await calendar_service.delete_plan(db, user=user, plan_id=plan_id)


@router.post("/{plan_id}/reminder", response_model=ContentPlanResponse)
async def set_reminder_endpoint(
    plan_id: uuid.UUID,
    payload: ReminderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPlanResponse:
    plan = await calendar_service.set_reminder(
        db, user=user, plan_id=plan_id, reminder_at=payload.reminder_at
    )
    return _to_response(plan)


@router.post("/{plan_id}/mark-posted", response_model=ContentPlanResponse)
async def mark_posted_endpoint(
    plan_id: uuid.UUID,
    payload: MarkContentPlanPostedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentPlanResponse:
    plan = await calendar_service.mark_posted(db, user=user, plan_id=plan_id, payload=payload)
    return _to_response(plan)


@router.post("/recurring-slots", response_model=list[ContentPlanResponse])
async def recurring_slots_endpoint(
    payload: RecurringSlotsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentPlanResponse]:
    plans = await calendar_service.create_recurring_slots(db, user=user, cadence=payload.cadence)
    return [_to_response(plan) for plan in plans]


@router.post("/bulk-schedule", response_model=list[ContentPlanResponse])
async def bulk_schedule_endpoint(
    payload: BulkScheduleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentPlanResponse]:
    plans = await calendar_service.bulk_schedule(
        db, user=user, cadence=payload.cadence, plan_ids=payload.plan_ids
    )
    return [_to_response(plan) for plan in plans]
