"""Resolves the role an audit scores against: the caller's own input if
given, otherwise inferred from the profile's current experience title.
Never guessed beyond that -- categories that need a target role and get
neither skip the relevant sub-check with an unlock message rather than
assume anything further."""

from __future__ import annotations

from app.profiles.schema import ProfileSnapshot


def resolve_target_role(
    snapshot: ProfileSnapshot, *, supplied: str | None
) -> tuple[str | None, bool]:
    """Returns `(target_role, was_assumed)`."""
    if supplied:
        return supplied, False
    if snapshot.experiences:
        for experience in snapshot.experiences:
            if experience.is_current and experience.title:
                return experience.title, True
    return None, False
