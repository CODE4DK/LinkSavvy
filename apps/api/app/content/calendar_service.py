"""The content calendar's domain logic: plan CRUD, cadence-driven
bulk-scheduling and recurring placeholders, reminders (enqueued
through Phase 4's job runner, sent via Phase 1's mail sender -- see
calendar_reminder_job.py), marking a plan posted, and the 12-week
consistency strip. Manual performance capture (Section 6) builds on
`ContentPlan.performance` but lives in its own module alongside the
Content audit integration it feeds.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.calendar_reminder_job import CONTENT_REMINDER_JOB_TYPE
from app.errors import ApiError, ErrorCode
from app.jobs.queue import enqueue
from app.models.content_plan import ContentPlan
from app.models.user import User
from app.schemas.content_plans import (
    Cadence,
    ContentPlanCreate,
    ContentPlanUpdate,
    MarkContentPlanPostedRequest,
    RescheduleRequest,
)

_CONSISTENCY_WEEKS = 12


def _cadence_dates(cadence: Cadence) -> list[date]:
    dates: list[date] = []
    for week in range(cadence.weeks):
        week_start = cadence.start_date + timedelta(weeks=week)
        week_monday = week_start - timedelta(days=week_start.weekday())
        for day in sorted(cadence.days_of_week):
            candidate = week_monday + timedelta(days=day)
            if candidate >= cadence.start_date:
                dates.append(candidate)
    return sorted(dates)


def _cadence_rule_string(cadence: Cadence) -> str:
    days = ",".join(str(d) for d in sorted(cadence.days_of_week))
    time_part = cadence.time.isoformat() if cadence.time else ""
    return f"weekly:{days}:{time_part}"


async def create_plan(db: AsyncSession, *, user: User, payload: ContentPlanCreate) -> ContentPlan:
    plan = ContentPlan(
        user_id=user.id,
        asset_id=payload.asset_id,
        title=payload.title,
        body_preview=payload.body_preview,
        content_type=payload.content_type,
        status=payload.status,
        planned_for=payload.planned_for,
        planned_time=payload.planned_time,
        tags=payload.tags,
        notes=payload.notes,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def get_owned_plan(db: AsyncSession, *, user: User, plan_id: uuid.UUID) -> ContentPlan:
    plan = await db.get(ContentPlan, plan_id)
    if plan is None or plan.user_id != user.id or plan.deleted_at is not None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such content plan")
    return plan


async def list_plans(db: AsyncSession, *, user: User, start: date, end: date) -> list[ContentPlan]:
    stmt = (
        select(ContentPlan)
        .where(
            ContentPlan.user_id == user.id,
            ContentPlan.deleted_at.is_(None),
            ContentPlan.planned_for >= start,
            ContentPlan.planned_for <= end,
        )
        .order_by(ContentPlan.planned_for, ContentPlan.planned_time)
    )
    return list((await db.execute(stmt)).scalars().all())


async def update_plan(
    db: AsyncSession, *, user: User, plan_id: uuid.UUID, payload: ContentPlanUpdate
) -> ContentPlan:
    plan = await get_owned_plan(db, user=user, plan_id=plan_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(plan, field, value)
    await db.commit()
    await db.refresh(plan)
    return plan


async def reschedule_plan(
    db: AsyncSession, *, user: User, plan_id: uuid.UUID, payload: RescheduleRequest
) -> ContentPlan:
    plan = await get_owned_plan(db, user=user, plan_id=plan_id)
    plan.planned_for = payload.planned_for
    plan.planned_time = payload.planned_time
    await db.commit()
    await db.refresh(plan)
    return plan


async def delete_plan(db: AsyncSession, *, user: User, plan_id: uuid.UUID) -> None:
    plan = await get_owned_plan(db, user=user, plan_id=plan_id)
    plan.deleted_at = datetime.now(UTC)
    await db.commit()


async def set_reminder(
    db: AsyncSession, *, user: User, plan_id: uuid.UUID, reminder_at: datetime | None
) -> ContentPlan:
    plan = await get_owned_plan(db, user=user, plan_id=plan_id)
    plan.reminder_at = reminder_at
    await db.commit()
    await db.refresh(plan)
    if reminder_at is not None:
        await enqueue(
            db,
            job_type=CONTENT_REMINDER_JOB_TYPE,
            payload={"content_plan_id": str(plan.id)},
            user_id=user.id,
            scheduled_for=reminder_at,
        )
    return plan


async def mark_posted(
    db: AsyncSession, *, user: User, plan_id: uuid.UUID, payload: MarkContentPlanPostedRequest
) -> ContentPlan:
    plan = await get_owned_plan(db, user=user, plan_id=plan_id)
    plan.status = "posted"
    plan.posted_at = payload.posted_at or datetime.now(UTC)
    if payload.linkedin_url is not None:
        plan.performance = {**plan.performance, "linkedin_url": payload.linkedin_url}
    if payload.performance is not None:
        numbers = payload.performance.model_dump(exclude_none=True)
        plan.performance = {**plan.performance, **numbers}
    await db.commit()
    await db.refresh(plan)
    return plan


async def create_recurring_slots(
    db: AsyncSession, *, user: User, cadence: Cadence
) -> list[ContentPlan]:
    rule = _cadence_rule_string(cadence)
    plans = []
    for slot_date in _cadence_dates(cadence):
        plan = ContentPlan(
            user_id=user.id,
            title="",
            body_preview="",
            status="idea",
            planned_for=slot_date,
            planned_time=cadence.time,
            recurrence_rule=rule,
        )
        db.add(plan)
        plans.append(plan)
    await db.commit()
    for plan in plans:
        await db.refresh(plan)
    return plans


async def bulk_schedule(
    db: AsyncSession, *, user: User, cadence: Cadence, plan_ids: list[uuid.UUID]
) -> list[ContentPlan]:
    dates = _cadence_dates(cadence)
    updated: list[ContentPlan] = []
    for plan_id, slot_date in zip(plan_ids, dates, strict=False):
        plan = await get_owned_plan(db, user=user, plan_id=plan_id)
        plan.planned_for = slot_date
        plan.planned_time = cadence.time
        if plan.status == "idea":
            plan.status = "scheduled"
        updated.append(plan)
    await db.commit()
    for plan in updated:
        await db.refresh(plan)
    return updated


async def consistency_strip(db: AsyncSession, *, user: User) -> list[tuple[date, int]]:
    today = datetime.now(UTC).date()
    this_monday = today - timedelta(days=today.weekday())
    earliest_monday = this_monday - timedelta(weeks=_CONSISTENCY_WEEKS - 1)

    stmt = select(ContentPlan).where(
        ContentPlan.user_id == user.id,
        ContentPlan.deleted_at.is_(None),
        ContentPlan.status == "posted",
        ContentPlan.posted_at.is_not(None),
    )
    posted_plans = (await db.execute(stmt)).scalars().all()

    counts: dict[date, int] = {
        earliest_monday + timedelta(weeks=i): 0 for i in range(_CONSISTENCY_WEEKS)
    }
    for plan in posted_plans:
        assert plan.posted_at is not None
        posted_date = plan.posted_at.date()
        week_monday = posted_date - timedelta(days=posted_date.weekday())
        if week_monday in counts:
            counts[week_monday] += 1

    return sorted(counts.items())
