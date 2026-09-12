"""Maps LinkedIn OIDC userinfo claims onto a ProfileSnapshot draft.

The `openid profile email` scope (the only one Phase 01 requested, and
the only one this app is approved for) grants exactly: sub, name,
given_name, family_name, picture, email, email_verified. That is all
LinkedIn will ever give us here — everything else on ProfileSnapshot is
left absent, never guessed. `available_fields` records which
ProfileSnapshot fields LinkedIn actually populated, so the UI can show
plainly which sections came from LinkedIn and which the user must
supply themselves.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.profiles.schema import FieldProvenance, Identity, ProfileSnapshot, ProfileSource


def map_linkedin_userinfo_to_snapshot(
    claims: dict[str, Any],
) -> tuple[ProfileSnapshot, list[str]]:
    full_name = claims.get("name")
    picture = claims.get("picture")

    available_fields: list[str] = []
    provenance: dict[str, FieldProvenance] = {}
    identity: Identity | None = None

    if full_name or picture:
        identity = Identity(full_name=full_name, profile_picture_url=picture)
        if full_name:
            available_fields.append("identity.full_name")
            provenance["/identity/full_name"] = FieldProvenance(
                source=ProfileSource.LINKEDIN_API, confidence=1.0
            )
        if picture:
            available_fields.append("identity.profile_picture_url")
            provenance["/identity/profile_picture_url"] = FieldProvenance(
                source=ProfileSource.LINKEDIN_API, confidence=1.0
            )

    snapshot = ProfileSnapshot(
        source=ProfileSource.LINKEDIN_API,
        captured_at=datetime.now(UTC),
        identity=identity,
        field_provenance=provenance,
    )
    return snapshot, available_fields
