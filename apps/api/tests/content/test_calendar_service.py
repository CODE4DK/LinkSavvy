from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.content import calendar_service
from app.content.calendar_reminder_job import CONTENT_REMINDER_JOB_TYPE
from app.errors import ApiError
from app.jobs.worker import run_once
from app.models.user import User
from app.schemas.content_plans import (
    Cadence,
    ContentPlanCreate,
    ContentPlanUpdate,
    MarkContentPlanPostedRequest,
    PerformanceNumbers,
    RescheduleRequest,
)


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"calendar-{uuid.uuid4()}@example.com", full_name="Calendar Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_create_and_get_plan(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session,
        user=user,
        payload=ContentPlanCreate(title="My idea", planned_for=date(2026, 6, 1)),
    )
    assert plan.status == "idea"
    fetched = await calendar_service.get_owned_plan(db_session, user=user, plan_id=plan.id)
    assert fetched.title == "My idea"


async def test_get_owned_plan_rejects_another_users_plan(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session)
    other = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session, user=owner, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
    )
    with pytest.raises(ApiError):
        await calendar_service.get_owned_plan(db_session, user=other, plan_id=plan.id)


async def test_list_plans_filters_by_date_range(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await calendar_service.create_plan(
        db_session,
        user=user,
        payload=ContentPlanCreate(title="in range", planned_for=date(2026, 6, 5)),
    )
    await calendar_service.create_plan(
        db_session,
        user=user,
        payload=ContentPlanCreate(title="out of range", planned_for=date(2026, 7, 5)),
    )
    plans = await calendar_service.list_plans(
        db_session, user=user, start=date(2026, 6, 1), end=date(2026, 6, 30)
    )
    assert [p.title for p in plans] == ["in range"]


async def test_update_plan_only_touches_provided_fields(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session,
        user=user,
        payload=ContentPlanCreate(title="Original", notes="keep me", planned_for=date(2026, 6, 1)),
    )
    updated = await calendar_service.update_plan(
        db_session,
        user=user,
        plan_id=plan.id,
        payload=ContentPlanUpdate(status="drafted"),
    )
    assert updated.status == "drafted"
    assert updated.title == "Original"
    assert updated.notes == "keep me"


async def test_reschedule_plan_changes_date(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session, user=user, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
    )
    rescheduled = await calendar_service.reschedule_plan(
        db_session,
        user=user,
        plan_id=plan.id,
        payload=RescheduleRequest(planned_for=date(2026, 6, 15)),
    )
    assert rescheduled.planned_for == date(2026, 6, 15)


async def test_delete_plan_soft_deletes(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session, user=user, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
    )
    await calendar_service.delete_plan(db_session, user=user, plan_id=plan.id)
    with pytest.raises(ApiError):
        await calendar_service.get_owned_plan(db_session, user=user, plan_id=plan.id)


async def test_mark_posted_sets_status_and_performance(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session, user=user, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
    )
    posted = await calendar_service.mark_posted(
        db_session,
        user=user,
        plan_id=plan.id,
        payload=MarkContentPlanPostedRequest(
            linkedin_url="https://www.linkedin.com/feed/update/urn:li:activity:1",
            performance=PerformanceNumbers(impressions=100, reactions=5),
        ),
    )
    assert posted.status == "posted"
    assert posted.posted_at is not None
    assert posted.performance["linkedin_url"].startswith("https://www.linkedin.com")
    assert posted.performance["impressions"] == 100
    assert posted.performance["reactions"] == 5


async def test_create_recurring_slots_generates_empty_placeholders(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    # A Monday.
    cadence = Cadence(days_of_week=[1, 3], start_date=date(2026, 6, 1), weeks=2)
    plans = await calendar_service.create_recurring_slots(db_session, user=user, cadence=cadence)
    assert len(plans) == 4
    for plan in plans:
        assert plan.status == "idea"
        assert plan.title == ""
        assert plan.recurrence_rule == "weekly:1,3:"
        assert plan.planned_for.weekday() in (1, 3)


async def test_bulk_schedule_assigns_existing_ideas_to_cadence_slots(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    idea_one = await calendar_service.create_plan(
        db_session,
        user=user,
        payload=ContentPlanCreate(title="Idea one", planned_for=date(2026, 1, 1)),
    )
    idea_two = await calendar_service.create_plan(
        db_session,
        user=user,
        payload=ContentPlanCreate(title="Idea two", planned_for=date(2026, 1, 1)),
    )
    cadence = Cadence(days_of_week=[1, 3], start_date=date(2026, 6, 1), weeks=2)
    scheduled = await calendar_service.bulk_schedule(
        db_session, user=user, cadence=cadence, plan_ids=[idea_one.id, idea_two.id]
    )
    assert len(scheduled) == 2
    for plan in scheduled:
        assert plan.status == "scheduled"
        assert plan.planned_for != date(2026, 1, 1)


async def test_consistency_strip_counts_posted_plans_by_week(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session, user=user, payload=ContentPlanCreate(planned_for=date(2026, 6, 1))
    )
    await calendar_service.mark_posted(
        db_session, user=user, plan_id=plan.id, payload=MarkContentPlanPostedRequest()
    )
    weeks = await calendar_service.consistency_strip(db_session, user=user)
    assert len(weeks) == 12
    assert sum(count for _, count in weeks) == 1


async def test_set_reminder_enqueues_and_worker_sends_email(
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[dict[str, str]] = []

    async def fake_send_email(*, to: str, subject: str, text_body: str, html_body: str) -> None:
        sent.append({"to": to, "subject": subject})

    monkeypatch.setattr("app.content.calendar_reminder_job.send_email", fake_send_email)

    user = await _create_user(db_session)
    plan = await calendar_service.create_plan(
        db_session,
        user=user,
        payload=ContentPlanCreate(title="Reminder me", planned_for=date(2026, 6, 1)),
    )
    reminder_at = datetime.now(UTC) - timedelta(minutes=1)
    await calendar_service.set_reminder(
        db_session, user=user, plan_id=plan.id, reminder_at=reminder_at
    )

    processed = await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    assert processed is True
    assert len(sent) == 1
    assert sent[0]["to"] == user.email
    assert CONTENT_REMINDER_JOB_TYPE == "content_reminder"
