from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.orchestrator import run_audit
from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot
from app.tools.context import ContextKey, ContextUnavailable, assemble

from ..audit.categories.conftest import empty_snapshot, rich_snapshot


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"tools-ctx-{uuid.uuid4()}@example.com", full_name="Context Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def test_template_var_replaces_dots_with_underscores() -> None:
    assert ContextKey.PROFILE_IDENTITY.template_var == "profile_identity"
    assert ContextKey.TARGET_ROLE.template_var == "target_role"


async def test_assemble_uses_extra_for_supplied_keys(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    context, included = await assemble(
        user=user,
        db=db_session,
        required=[ContextKey.USER_SUPPLIED_TEXT],
        optional=[],
        token_budget=10_000,
        extra={ContextKey.USER_SUPPLIED_TEXT: "make it punchier"},
    )
    assert included == [ContextKey.USER_SUPPLIED_TEXT]
    assert "make it punchier" in context["user_supplied_text"]
    assert context["user_supplied_text"].startswith("## User-supplied text")


async def test_assemble_raises_context_unavailable_for_missing_required_extra(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    try:
        await assemble(
            user=user,
            db=db_session,
            required=[ContextKey.TARGET_ROLE],
            optional=[],
            token_budget=10_000,
        )
        raise AssertionError("expected ContextUnavailable")
    except ContextUnavailable as exc:
        assert exc.key is ContextKey.TARGET_ROLE
        assert "target role" in exc.reason


async def test_assemble_raises_context_unavailable_with_no_snapshot(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    try:
        await assemble(
            user=user,
            db=db_session,
            required=[ContextKey.PROFILE_HEADLINE],
            optional=[],
            token_budget=10_000,
        )
        raise AssertionError("expected ContextUnavailable")
    except ContextUnavailable as exc:
        assert exc.key is ContextKey.PROFILE_HEADLINE
        assert exc.fix  # a concrete next step, not empty


async def test_assemble_pulls_profile_fields_from_the_active_snapshot(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    context, included = await assemble(
        user=user,
        db=db_session,
        required=[ContextKey.PROFILE_HEADLINE],
        optional=[ContextKey.PROFILE_SKILLS, ContextKey.PROFILE_EXPERIENCES],
        token_budget=10_000,
    )
    assert set(included) == {
        ContextKey.PROFILE_HEADLINE,
        ContextKey.PROFILE_SKILLS,
        ContextKey.PROFILE_EXPERIENCES,
    }
    assert "Senior Backend Engineer" in context["profile_headline"]
    assert "Python" in context["profile_skills"]
    assert "Acme Corp" in context["profile_experiences"]


async def test_assemble_skips_optional_keys_with_nothing_to_say(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=empty_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    context, included = await assemble(
        user=user,
        db=db_session,
        required=[],
        optional=[ContextKey.PROFILE_SKILLS, ContextKey.PROFILE_ABOUT],
        token_budget=10_000,
    )
    assert included == []
    assert context == {}


async def test_assemble_drops_lowest_priority_optional_key_over_budget(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    # PROFILE_FULL (priority 20) is the lowest-priority key here and
    # dwarfs the tiny budget on its own -- it should be dropped whole,
    # while the higher-priority, cheap PROFILE_HEADLINE survives.
    context, included = await assemble(
        user=user,
        db=db_session,
        required=[ContextKey.PROFILE_HEADLINE],
        optional=[ContextKey.PROFILE_FULL],
        token_budget=20,
    )
    assert ContextKey.PROFILE_HEADLINE in included
    assert ContextKey.PROFILE_FULL not in included
    assert "profile_full" not in context


async def test_assemble_never_drops_a_required_key_even_over_budget(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    context, included = await assemble(
        user=user,
        db=db_session,
        required=[ContextKey.PROFILE_FULL],
        optional=[],
        token_budget=1,
    )
    assert included == [ContextKey.PROFILE_FULL]
    assert "profile_full" in context


async def test_assemble_includes_latest_audit_findings(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    snapshot_row = await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()
    await run_audit(user=user, db=db_session, snapshot_row=snapshot_row, trigger="manual")

    context, included = await assemble(
        user=user,
        db=db_session,
        required=[],
        optional=[ContextKey.AUDIT_LATEST_FINDINGS],
        token_budget=10_000,
    )
    assert included == [ContextKey.AUDIT_LATEST_FINDINGS]
    assert "audit_latest_findings" in context


async def test_voice_profile_falls_back_to_the_neutral_default(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    context, included = await assemble(
        user=user,
        db=db_session,
        required=[],
        optional=[ContextKey.VOICE_PROFILE],
        token_budget=10_000,
    )
    assert included == [ContextKey.VOICE_PROFILE]
    assert "clear" in context["voice_profile"]
    assert "neutral default" in context["voice_profile"]


async def test_voice_profile_reflects_a_derived_descriptor(db_session: AsyncSession) -> None:
    from app.content.voice_service import MIN_SAMPLES, submit_voice_samples

    user = await _create_user(db_session)
    texts = [f"Sample post number {i} about distributed systems." for i in range(MIN_SAMPLES)]
    await submit_voice_samples(db_session, user=user, texts=texts, source="paste")

    context, included = await assemble(
        user=user,
        db=db_session,
        required=[],
        optional=[ContextKey.VOICE_PROFILE],
        token_budget=10_000,
    )
    assert included == [ContextKey.VOICE_PROFILE]
    assert "direct" in context["voice_profile"]
