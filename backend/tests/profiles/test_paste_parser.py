from app.profiles.parsers.paste import parse_paste, parsed_profile_to_snapshot
from app.profiles.schema import ProfileSource

SAMPLE_PASTE = """\
Jane Doe
Senior Backend Engineer at Acme Inc | Python, Distributed Systems
San Francisco, CA

About
Building reliable backend systems for a decade. Passionate about mentoring.
Currently focused on distributed systems at scale.

Experience
Senior Backend Engineer
Acme Inc · Full-time
Jan 2021 - Present · 3 yrs 8 mos
San Francisco, CA
Led the platform team.
• Rebuilt the billing pipeline
• Mentored four engineers
• Cut p99 latency by 40%

Software Engineer
Old Co · Full-time
Jun 2018 - Dec 2020 · 2 yrs 7 mos
Remote
Worked on the search team.

Education
State University
Bachelor of Science, Computer Science
2014 - 2018

Licenses & certifications
AWS Certified Solutions Architect
Amazon Web Services
Issued Mar 2022
Credential ID ABC123

Skills
Python · 42 endorsements
Distributed Systems
SQL · 10 endorsements

Languages
English
Native or bilingual proficiency

Spanish - Professional working proficiency
"""


def test_parses_identity_from_header() -> None:
    parsed = parse_paste(SAMPLE_PASTE)

    assert parsed.identity is not None
    assert parsed.identity.full_name == "Jane Doe"
    assert (
        parsed.identity.headline
        == "Senior Backend Engineer at Acme Inc | Python, Distributed Systems"
    )
    assert parsed.identity.location == "San Francisco, CA"


def test_parses_about_section() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    assert parsed.about is not None
    assert "Building reliable backend systems" in parsed.about


def test_parses_two_experience_entries_with_bullets_and_dates() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    assert parsed.experiences is not None
    assert len(parsed.experiences) == 2

    current = parsed.experiences[0]
    assert current.company == "Acme Inc"
    assert current.title == "Senior Backend Engineer"
    assert current.employment_type == "Full-time"
    assert current.is_current is True
    assert current.start is not None and current.start.year == 2021 and current.start.month == 1
    assert current.end is None
    assert current.bullets == [
        "Rebuilt the billing pipeline",
        "Mentored four engineers",
        "Cut p99 latency by 40%",
    ]
    assert current.location == "San Francisco, CA"

    previous = parsed.experiences[1]
    assert previous.company == "Old Co"
    assert previous.title == "Software Engineer"
    assert previous.is_current is False
    assert previous.start is not None and previous.start.month == 6
    assert previous.end is not None and previous.end.year == 2020 and previous.end.month == 12


def test_parses_education() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    assert parsed.education is not None
    assert len(parsed.education) == 1
    edu = parsed.education[0]
    assert edu.school == "State University"
    assert edu.degree == "Bachelor of Science"
    assert edu.field == "Computer Science"
    assert edu.start_year == 2014
    assert edu.end_year == 2018


def test_parses_certifications() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    assert parsed.certifications is not None
    cert = parsed.certifications[0]
    assert cert.name == "AWS Certified Solutions Architect"
    assert cert.issuer == "Amazon Web Services"
    assert cert.issued is not None and cert.issued.year == 2022 and cert.issued.month == 3
    assert cert.credential_id == "ABC123"


def test_parses_skills_with_and_without_endorsements() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    assert parsed.skills is not None
    by_name = {skill.name: skill for skill in parsed.skills}
    assert by_name["Python"].endorsements == 42
    assert by_name["Distributed Systems"].endorsements is None
    assert by_name["SQL"].endorsements == 10


def test_parses_languages() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    assert parsed.languages is not None
    assert parsed.languages[0].name == "English"
    assert parsed.languages[0].proficiency == "Native or bilingual proficiency"
    assert parsed.languages[1].name == "Spanish"
    assert parsed.languages[1].proficiency == "Professional working proficiency"


def test_sample_paste_produces_no_warnings() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    assert parsed.warnings == []


def test_unparseable_experience_entry_is_kept_with_a_warning() -> None:
    text = "Someone\nA Headline\n\nExperience\nJust some free text with no date range at all\n"
    parsed = parse_paste(text)

    assert parsed.experiences is not None
    assert len(parsed.experiences) == 1
    assert parsed.experiences[0].description == "Just some free text with no date range at all"
    assert any("date range" in warning for warning in parsed.warnings)


def test_deduplicates_adjacent_repeated_company_line() -> None:
    text = (
        "Experience\n"
        "Engineer\n"
        "Acme Inc\n"
        "Acme Inc · Full-time\n"
        "Jan 2020 - Present · 1 yr\n"
    )
    parsed = parse_paste(text)
    assert parsed.experiences is not None
    assert parsed.experiences[0].company == "Acme Inc"


def test_text_with_no_known_headings_warns_but_does_not_crash() -> None:
    parsed = parse_paste("Just some random text\nwith no structure at all.")
    assert parsed.identity is not None
    assert parsed.identity.full_name == "Just some random text"
    assert any("No recognised section headings" in warning for warning in parsed.warnings)


def test_parsed_profile_to_snapshot_sets_source_and_provenance() -> None:
    parsed = parse_paste(SAMPLE_PASTE)
    snapshot = parsed_profile_to_snapshot(parsed, source=ProfileSource.PASTE)

    assert snapshot.source == ProfileSource.PASTE
    assert snapshot.identity is not None
    assert "/identity" in snapshot.field_provenance
    assert snapshot.field_provenance["/identity"].source == ProfileSource.PASTE
    assert "/languages" not in snapshot.field_provenance or snapshot.languages is not None
