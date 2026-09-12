from datetime import UTC, datetime

from app.profiles.diff import FieldChangeResult, diff_snapshots
from app.profiles.schema import Experience, Identity, ProfileSnapshot, ProfileSource, Skill


def _snapshot(**kwargs: object) -> ProfileSnapshot:
    return ProfileSnapshot(
        source=ProfileSource.MANUAL, captured_at=datetime.now(UTC), **kwargs  # type: ignore[arg-type]
    )


def test_no_changes_yields_empty_diff() -> None:
    snapshot = _snapshot(identity=Identity(full_name="Jane"))
    result = diff_snapshots(snapshot, snapshot)
    assert result.field_changes == []
    assert result.list_changes == {}


def test_detects_identity_field_change() -> None:
    before = _snapshot(identity=Identity(full_name="Jane", headline="Engineer"))
    after = _snapshot(identity=Identity(full_name="Jane", headline="Staff Engineer"))

    result = diff_snapshots(before, after)

    assert len(result.field_changes) == 1
    change = result.field_changes[0]
    assert change.path == "/identity/headline"
    assert change.before == "Engineer"
    assert change.after == "Staff Engineer"


def test_detects_about_change() -> None:
    before = _snapshot(about="Old bio")
    after = _snapshot(about="New bio")
    result = diff_snapshots(before, after)
    assert result.field_changes == [
        FieldChangeResult(path="/about", before="Old bio", after="New bio")
    ]


def test_added_and_removed_experiences_matched_by_stable_key() -> None:
    before = _snapshot(experiences=[Experience(company="Acme", title="Engineer")])
    after = _snapshot(experiences=[Experience(company="Acme", title="Senior Engineer")])

    result = diff_snapshots(before, after)
    changes = result.list_changes["experiences"]
    kinds = {c.change for c in changes}
    assert kinds == {"added", "removed"}


def test_modified_skill_reports_field_level_changes() -> None:
    before = _snapshot(skills=[Skill(name="Python", endorsements=5)])
    after = _snapshot(skills=[Skill(name="Python", endorsements=42)])

    result = diff_snapshots(before, after)
    changes = result.list_changes["skills"]
    assert len(changes) == 1
    assert changes[0].change == "modified"
    assert changes[0].field_changes[0].path == "endorsements"
    assert changes[0].field_changes[0].before == 5
    assert changes[0].field_changes[0].after == 42


def test_unchanged_list_items_produce_no_change_entry() -> None:
    skill = Skill(name="Python", endorsements=5)
    before = _snapshot(skills=[skill])
    after = _snapshot(skills=[skill])
    result = diff_snapshots(before, after)
    assert "skills" not in result.list_changes


def test_reordering_a_list_is_not_reported_as_changes() -> None:
    before = _snapshot(skills=[Skill(name="Python"), Skill(name="SQL")])
    after = _snapshot(skills=[Skill(name="SQL"), Skill(name="Python")])
    result = diff_snapshots(before, after)
    assert "skills" not in result.list_changes


def test_absent_and_empty_list_are_both_treated_as_no_items() -> None:
    before = _snapshot(skills=None)
    after = _snapshot(skills=[])
    result = diff_snapshots(before, after)
    assert "skills" not in result.list_changes
