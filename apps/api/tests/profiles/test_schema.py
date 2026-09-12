from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.profiles.schema import (
    Experience,
    FieldProvenance,
    Identity,
    ProfileSnapshot,
    ProfileSource,
)


def test_minimal_snapshot_leaves_everything_else_absent() -> None:
    snapshot = ProfileSnapshot(source=ProfileSource.MANUAL, captured_at=datetime.now(UTC))

    assert snapshot.identity is None
    assert snapshot.about is None
    assert snapshot.experiences is None
    assert snapshot.field_provenance == {}


def test_empty_list_is_distinct_from_absent_list() -> None:
    known_to_have_none = ProfileSnapshot(
        source=ProfileSource.MANUAL, captured_at=datetime.now(UTC), experiences=[]
    )
    unknown = ProfileSnapshot(source=ProfileSource.MANUAL, captured_at=datetime.now(UTC))

    assert known_to_have_none.experiences == []
    assert unknown.experiences is None
    assert known_to_have_none.experiences != unknown.experiences


def test_blank_string_is_distinct_from_absent_string() -> None:
    blank = Identity(headline="")
    absent = Identity()

    assert blank.headline == ""
    assert absent.headline is None


def test_field_provenance_round_trips_through_json() -> None:
    snapshot = ProfileSnapshot(
        source=ProfileSource.LINKEDIN_API,
        captured_at=datetime.now(UTC),
        identity=Identity(full_name="Ada Lovelace"),
        field_provenance={
            "/identity/full_name": FieldProvenance(
                source=ProfileSource.LINKEDIN_API, confidence=1.0
            )
        },
    )

    restored = ProfileSnapshot.model_validate_json(snapshot.model_dump_json())

    assert restored.identity is not None
    assert restored.identity.full_name == "Ada Lovelace"
    assert restored.field_provenance["/identity/full_name"].confidence == 1.0


def test_experience_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Experience.model_validate({"company": "Acme", "not_a_real_field": True})


def test_confidence_must_be_within_unit_interval() -> None:
    with pytest.raises(ValidationError):
        FieldProvenance(source=ProfileSource.PASTE, confidence=1.5)
