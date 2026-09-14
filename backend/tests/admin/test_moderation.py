from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import moderation
from app.models.user import User


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(email=f"mod-test-{uuid.uuid4()}@example.com", full_name="Mod Tester", **kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_flag_ai_policy_violation_lands_in_pending_queue(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await moderation.flag_ai_policy_violation(
        db_session,
        user_id=user.id,
        target_type="conversation",
        target_id="abc",
        reason="output policy: action_claim",
        content="I already posted that for you on LinkedIn.",
    )
    await db_session.commit()

    flags = await moderation.list_flags(db_session, status="pending")
    assert len(flags) == 1
    assert flags[0].source == "ai_policy"


async def test_review_flag_marks_reviewed_and_writes_audit_log(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    reporter = await _create_user(db_session)
    flag = await moderation.report_content(
        db_session,
        reporter_user_id=reporter.id,
        target_type="asset",
        target_id="xyz",
        reason="spam",
        excerpt="buy my course",
    )

    reviewed = await moderation.review_flag(
        db_session, admin_id=admin.id, flag_id=flag.id, status="removed", note="confirmed spam"
    )
    assert reviewed.status == "removed"
    assert reviewed.reviewed_by == admin.id
    assert reviewed.review_note == "confirmed spam"

    depth = await moderation.queue_depth(db_session)
    assert depth == 0
