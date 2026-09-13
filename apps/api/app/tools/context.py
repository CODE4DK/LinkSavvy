"""Assembles the labelled context blocks a tool's prompt renders.

Each `ContextKey` has exactly one serializer and one priority, so a
tool's `required_context`/`optional_context` lists (declared on its
`ToolDefinition`) are the only place that decides what a prompt can
see -- `assemble()` itself never branches on a tool id. When the token
budget is exceeded, the lowest-priority *optional* key is dropped
whole (never truncated mid-record); a required key is never dropped --
if one has nothing to serialize, `assemble()` raises `ContextUnavailable`
naming exactly what's missing and how to fix it, so the client can turn
that into an actionable prompt instead of a generic failure.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.user import User
from app.profiles.schema import ProfileSnapshot
from app.profiles.service import get_active_snapshot

# The same cheap estimate app/ai/providers/fake_provider.py uses for
# token accounting -- good enough for "should we drop a block", not
# meant to match a real tokenizer exactly.
_CHARS_PER_TOKEN = 4


class ContextKey(StrEnum):
    PROFILE_IDENTITY = "profile.identity"
    PROFILE_HEADLINE = "profile.headline"
    PROFILE_ABOUT = "profile.about"
    PROFILE_EXPERIENCES = "profile.experiences"
    PROFILE_SKILLS = "profile.skills"
    PROFILE_FULL = "profile.full"
    AUDIT_LATEST_FINDINGS = "audit.latest_findings"
    TARGET_ROLE = "target_role"
    VOICE_PROFILE = "voice_profile"
    RECENT_ASSETS = "recent_assets"
    USER_SUPPLIED_TEXT = "user_supplied_text"

    @property
    def template_var(self) -> str:
        """The flat variable name a prompt template uses -- the
        sandboxed Jinja environment (app/ai/prompts/render.py) forbids
        attribute access, so a dotted key can't be referenced as
        `{{ profile.identity }}` directly."""
        return self.value.replace(".", "_")


class ContextUnavailable(ApiError):
    """A required context key had nothing to serialize -- e.g. no
    profile snapshot exists yet, or a required input field was left
    blank. Names exactly what's missing and how to fix it."""

    def __init__(self, key: ContextKey, *, reason: str, fix: str) -> None:
        self.key = key
        self.reason = reason
        self.fix = fix
        super().__init__(
            ErrorCode.VALIDATION_FAILED,
            f"can't run this tool: {reason}",
            details={"context_key": key.value, "reason": reason, "fix": fix},
        )


# Higher survives a budget cut first.
_PRIORITY: dict[ContextKey, int] = {
    ContextKey.USER_SUPPLIED_TEXT: 100,
    ContextKey.TARGET_ROLE: 90,
    ContextKey.PROFILE_HEADLINE: 80,
    ContextKey.PROFILE_ABOUT: 80,
    ContextKey.PROFILE_IDENTITY: 70,
    ContextKey.PROFILE_EXPERIENCES: 60,
    ContextKey.PROFILE_SKILLS: 60,
    ContextKey.AUDIT_LATEST_FINDINGS: 50,
    ContextKey.VOICE_PROFILE: 40,
    ContextKey.RECENT_ASSETS: 30,
    ContextKey.PROFILE_FULL: 20,
}

_LABELS: dict[ContextKey, str] = {
    ContextKey.PROFILE_IDENTITY: "Identity",
    ContextKey.PROFILE_HEADLINE: "Current headline",
    ContextKey.PROFILE_ABOUT: "Current About section",
    ContextKey.PROFILE_EXPERIENCES: "Experience",
    ContextKey.PROFILE_SKILLS: "Skills",
    ContextKey.PROFILE_FULL: "Full profile (JSON)",
    ContextKey.AUDIT_LATEST_FINDINGS: "Latest audit findings",
    ContextKey.TARGET_ROLE: "Target role",
    ContextKey.VOICE_PROFILE: "Voice profile",
    ContextKey.RECENT_ASSETS: "Recently saved assets",
    ContextKey.USER_SUPPLIED_TEXT: "User-supplied text",
}

_UNAVAILABLE_MESSAGES: dict[ContextKey, tuple[str, str]] = {
    ContextKey.PROFILE_IDENTITY: (
        "no profile snapshot has been committed yet",
        "Complete onboarding, or paste/upload your profile in Profile Hub.",
    ),
    ContextKey.PROFILE_HEADLINE: (
        "your profile has no headline yet",
        "Add a headline to your profile first.",
    ),
    ContextKey.PROFILE_ABOUT: (
        "your profile has no About section yet",
        "Add an About section to your profile first.",
    ),
    ContextKey.PROFILE_EXPERIENCES: (
        "your profile has no work experience listed",
        "Add at least one role to your profile first.",
    ),
    ContextKey.PROFILE_SKILLS: (
        "your profile has no skills listed",
        "Add some skills to your profile first.",
    ),
    ContextKey.PROFILE_FULL: (
        "no profile snapshot has been committed yet",
        "Complete onboarding, or paste/upload your profile in Profile Hub.",
    ),
    ContextKey.AUDIT_LATEST_FINDINGS: (
        "no audit has been run yet",
        "Run an audit from the Dashboard first.",
    ),
    ContextKey.TARGET_ROLE: (
        "this tool needs a target role",
        "Fill in the target role field.",
    ),
    ContextKey.VOICE_PROFILE: (
        "no voice profile is available yet",
        "This feature isn't available yet.",
    ),
    ContextKey.RECENT_ASSETS: (
        "you have no saved assets yet",
        "Save something to your Workspace first.",
    ),
    ContextKey.USER_SUPPLIED_TEXT: (
        "this tool needs some text to work with",
        "Fill in the text field.",
    ),
}

_PROFILE_SNAPSHOT_KEYS = frozenset(
    {
        ContextKey.PROFILE_IDENTITY,
        ContextKey.PROFILE_HEADLINE,
        ContextKey.PROFILE_ABOUT,
        ContextKey.PROFILE_EXPERIENCES,
        ContextKey.PROFILE_SKILLS,
        ContextKey.PROFILE_FULL,
    }
)

Serializer = Callable[..., Awaitable[str | None]]


async def _serialize_identity(*, snapshot: ProfileSnapshot | None, **_: Any) -> str | None:
    if snapshot is None or snapshot.identity is None:
        return None
    identity = snapshot.identity
    lines = [
        f"{label}: {value}"
        for label, value in (
            ("Name", identity.full_name),
            ("Headline", identity.headline),
            ("Industry", identity.industry),
            ("Location", identity.location),
        )
        if value
    ]
    return "\n".join(lines) or None


async def _serialize_headline(*, snapshot: ProfileSnapshot | None, **_: Any) -> str | None:
    if snapshot is None or snapshot.identity is None:
        return None
    return snapshot.identity.headline or None


async def _serialize_about(*, snapshot: ProfileSnapshot | None, **_: Any) -> str | None:
    if snapshot is None:
        return None
    return snapshot.about or None


async def _serialize_experiences(*, snapshot: ProfileSnapshot | None, **_: Any) -> str | None:
    if snapshot is None or not snapshot.experiences:
        return None
    blocks: list[str] = []
    for experience in snapshot.experiences:
        header = " at ".join(part for part in (experience.title, experience.company) if part)
        header = header or "Role"
        if experience.is_current:
            header += " (current)"
        lines = [header]
        if experience.description:
            lines.append(experience.description)
        lines.extend(f"- {bullet}" for bullet in experience.bullets or [])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) or None


async def _serialize_skills(*, snapshot: ProfileSnapshot | None, **_: Any) -> str | None:
    if snapshot is None or not snapshot.skills:
        return None
    names = [skill.name for skill in snapshot.skills if skill.name]
    return ", ".join(names) or None


async def _serialize_full(*, snapshot: ProfileSnapshot | None, **_: Any) -> str | None:
    if snapshot is None:
        return None
    return snapshot.model_dump_json(exclude={"field_provenance"}, exclude_none=True)


async def _serialize_latest_findings(*, user: User, db: AsyncSession, **_: Any) -> str | None:
    from app.audit.service import get_findings_by_category, get_latest_audit

    audit = await get_latest_audit(db, user_id=user.id)
    if audit is None:
        return None
    findings_by_category = await get_findings_by_category(db, audit_id=audit.id)
    lines = [
        f"- [{finding.severity}] {finding.title}"
        for findings in findings_by_category.values()
        for finding in findings
    ]
    return "\n".join(lines) or None


async def _serialize_recent_assets(*, user: User, db: AsyncSession, **_: Any) -> str | None:
    # Wired up once the `assets` table lands (this same phase's next
    # section) -- deferred rather than importing a model that doesn't
    # exist yet, so this module stays independently correct in the
    # meantime.
    return None


async def _serialize_voice_profile(**_: Any) -> str | None:
    # No voice-profile source exists yet -- that's a later phase's
    # feature, built from a corpus of the user's own writing. Always
    # unavailable rather than guessed, same as Phase 4's
    # career.resume_presence before the Career Hub added resume upload.
    return None


def _make_extra_serializer(key: ContextKey) -> Serializer:
    async def _serializer(*, extra: dict[ContextKey, str], **_: Any) -> str | None:
        return extra.get(key)

    return _serializer


_SERIALIZERS: dict[ContextKey, Serializer] = {
    ContextKey.PROFILE_IDENTITY: _serialize_identity,
    ContextKey.PROFILE_HEADLINE: _serialize_headline,
    ContextKey.PROFILE_ABOUT: _serialize_about,
    ContextKey.PROFILE_EXPERIENCES: _serialize_experiences,
    ContextKey.PROFILE_SKILLS: _serialize_skills,
    ContextKey.PROFILE_FULL: _serialize_full,
    ContextKey.AUDIT_LATEST_FINDINGS: _serialize_latest_findings,
    ContextKey.TARGET_ROLE: _make_extra_serializer(ContextKey.TARGET_ROLE),
    ContextKey.VOICE_PROFILE: _serialize_voice_profile,
    ContextKey.RECENT_ASSETS: _serialize_recent_assets,
    ContextKey.USER_SUPPLIED_TEXT: _make_extra_serializer(ContextKey.USER_SUPPLIED_TEXT),
}


def _label(key: ContextKey, body: str) -> str:
    return f"## {_LABELS[key]}\n{body}"


async def assemble(
    *,
    user: User,
    db: AsyncSession,
    required: list[ContextKey],
    optional: list[ContextKey],
    token_budget: int,
    extra: dict[ContextKey, str] | None = None,
) -> tuple[dict[str, Any], list[ContextKey]]:
    """Returns `(context, included)` -- `context` maps each included
    key's flat template variable name to its labelled block, ready to
    hand straight to `gateway.run()`; `included` is the exact list of
    `ContextKey`s that made it in, for the caller to record on the
    `ToolRun` so an output can always be traced back to its inputs.
    """
    extra = extra or {}
    ordered_keys = list(dict.fromkeys([*required, *optional]))

    snapshot: ProfileSnapshot | None = None
    if any(key in _PROFILE_SNAPSHOT_KEYS for key in ordered_keys):
        row = await get_active_snapshot(db, user_id=user.id)
        if row is not None:
            snapshot = ProfileSnapshot.model_validate(row.payload)

    raw: dict[ContextKey, str] = {}
    for key in ordered_keys:
        value = await _SERIALIZERS[key](user=user, db=db, snapshot=snapshot, extra=extra)
        if value:
            raw[key] = value

    missing_required = [key for key in required if key not in raw]
    if missing_required:
        key = missing_required[0]
        reason, fix = _UNAVAILABLE_MESSAGES[key]
        raise ContextUnavailable(key, reason=reason, fix=fix)

    included = [key for key in ordered_keys if key in raw]

    def _cost(key: ContextKey) -> int:
        return max(1, len(raw[key]) // _CHARS_PER_TOKEN)

    total = sum(_cost(key) for key in included)
    if total > token_budget:
        required_set = set(required)
        droppable = sorted(
            (key for key in included if key not in required_set),
            key=lambda key: _PRIORITY[key],
        )
        for key in droppable:
            if total <= token_budget:
                break
            total -= _cost(key)
            included.remove(key)

    context = {key.template_var: _label(key, raw[key]) for key in included}
    return context, included
