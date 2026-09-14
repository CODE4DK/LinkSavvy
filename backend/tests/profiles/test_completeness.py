from datetime import UTC, datetime

from app.profiles.completeness import compute_completeness
from app.profiles.schema import (
    DatePart,
    Experience,
    Identity,
    ProfileSnapshot,
    ProfileSource,
    Project,
    Skill,
)


def _partial_profile() -> ProfileSnapshot:
    """A hand-designed fixture where every rule's outcome is unambiguous.

    Passes: headline (15), about (15), min-experiences (20),
    current-role-bullets (15), min-skills (15), profile-photo (5) = 85
    Fails: certification-or-project (10), custom-url (5)
    """
    return ProfileSnapshot(
        source=ProfileSource.MANUAL,
        captured_at=datetime.now(UTC),
        identity=Identity(
            headline="X" * 50,  # > 40 chars
            custom_url=None,
            profile_picture_url="https://example.com/photo.jpg",
        ),
        about="Sentence one. Sentence two. Sentence three.",
        experiences=[
            Experience(
                company="Acme",
                title="Senior Engineer",
                start=DatePart(year=2020, month=1),
                is_current=True,
                bullets=["Did a thing", "Did another thing", "Did a third thing"],
            ),
            Experience(
                company="Old Co",
                title="Engineer",
                start=DatePart(year=2016, month=1),
                end=DatePart(year=2019, month=12),
                is_current=False,
            ),
        ],
        skills=[Skill(name=f"Skill {i}") for i in range(10)],
        certifications=None,
        projects=None,
    )


def test_completeness_matches_hand_computed_score() -> None:
    result = compute_completeness(_partial_profile())

    assert result.score == 85

    gap_codes = {gap.code for gap in result.gaps}
    assert gap_codes == {"has_certification_or_project", "has_custom_url"}

    assert result.section_breakdown["about"].earned == 15
    assert result.section_breakdown["about"].possible == 15
    assert result.section_breakdown["experience"].earned == 35
    assert result.section_breakdown["experience"].possible == 35
    assert result.section_breakdown["certifications_and_projects"].earned == 0
    assert result.section_breakdown["certifications_and_projects"].possible == 10
    assert result.section_breakdown["identity"].earned == 20
    assert result.section_breakdown["identity"].possible == 25


def test_completeness_is_deterministic() -> None:
    profile = _partial_profile()
    first = compute_completeness(profile)
    second = compute_completeness(profile)

    assert first.score == second.score
    assert first.gaps == second.gaps


def test_empty_profile_scores_zero() -> None:
    empty = ProfileSnapshot(source=ProfileSource.MANUAL, captured_at=datetime.now(UTC))
    result = compute_completeness(empty)

    assert result.score == 0
    assert len(result.gaps) == 8


def test_fully_complete_profile_scores_100() -> None:
    complete = ProfileSnapshot(
        source=ProfileSource.MANUAL,
        captured_at=datetime.now(UTC),
        identity=Identity(
            headline="Y" * 50,
            custom_url="janedoe",
            profile_picture_url="https://example.com/photo.jpg",
        ),
        about="Sentence one. Sentence two. Sentence three. Sentence four.",
        experiences=[
            Experience(
                company="Acme",
                title="Senior Engineer",
                is_current=True,
                bullets=["One", "Two", "Three"],
            ),
            Experience(company="Old Co", title="Engineer", is_current=False),
        ],
        skills=[Skill(name=f"Skill {i}") for i in range(12)],
        certifications=[],
        projects=[Project(name="Side Project")],
    )

    result = compute_completeness(complete)

    assert result.score == 100
    assert result.gaps == []
