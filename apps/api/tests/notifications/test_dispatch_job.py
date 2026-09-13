from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.jobs.queue import enqueue
from app.jobs.worker import run_once
from app.models.email_log import EmailLog
from app.models.notification import Notification
from app.models.user import User
from app.notifications import service
from app.notifications.dispatch_job import DISPATCH_JOB_TYPE


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"dispatch-{uuid.uuid4()}@example.com", full_name="Dispatch Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_dispatch_job_creates_notification_and_sends_email(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    await enqueue(
        db_session,
        job_type=DISPATCH_JOB_TYPE,
        payload={
            "type": "audit.completed",
            "title": "Your audit is ready",
            "body": "Score: 82",
            "action_route": "/dashboard",
        },
        user_id=user.id,
    )

    processed = await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    assert processed is True

    notification = (
        await db_session.execute(select(Notification).where(Notification.user_id == user.id))
    ).scalar_one()
    assert notification.title == "Your audit is ready"
    assert notification.read_at is None

    log = (
        await db_session.execute(select(EmailLog).where(EmailLog.user_id == user.id))
    ).scalar_one()
    assert log.status == "sent"
    assert log.template == "audit.completed"


async def test_dispatch_job_skips_email_when_channel_disabled(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    await service.set_preference(
        db_session,
        user_id=user.id,
        channel="email",
        notification_type="audit.completed",
        enabled=False,
    )
    await enqueue(
        db_session,
        job_type=DISPATCH_JOB_TYPE,
        payload={"type": "audit.completed", "title": "t", "body": "b"},
        user_id=user.id,
    )

    await run_once(worker_id="test-worker", session_factory=db_sessionmaker)

    notification = (
        await db_session.execute(select(Notification).where(Notification.user_id == user.id))
    ).scalar_one()
    assert notification is not None

    logs = (
        (await db_session.execute(select(EmailLog).where(EmailLog.user_id == user.id)))
        .scalars()
        .all()
    )
    assert logs == []
