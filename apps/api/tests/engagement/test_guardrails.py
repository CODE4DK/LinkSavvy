from __future__ import annotations

from app.engagement.guardrails import (
    OUTREACH_DAILY_SOFT_CAP,
    annotate_variant,
    make_variants_postprocessor,
    personalisation_check,
    soft_cap_warning,
    spam_tone_check,
)


def test_personalisation_check_passes_silently_with_no_context() -> None:
    assert personalisation_check("Hey! Would love to connect.", {}) == []
    assert personalisation_check("Hey! Would love to connect.", {"headline": ""}) == []


def test_personalisation_check_flags_generic_message() -> None:
    flags = personalisation_check(
        "Hey! Would love to connect and grow our networks together.",
        {"headline": "Senior Platform Engineer building distributed systems at Acme"},
    )
    assert len(flags) == 1
    assert "generic" in flags[0].lower() or "specific" in flags[0].lower()


def test_personalisation_check_passes_when_output_references_context() -> None:
    flags = personalisation_check(
        "Your work on distributed systems at Acme really stood out to me.",
        {"headline": "Senior Platform Engineer building distributed systems at Acme"},
    )
    assert flags == []


def test_spam_tone_check_flags_flattery() -> None:
    flags = spam_tone_check("Your profile is amazing, I'd love to connect.")
    assert any("flattery" in f for f in flags)


def test_spam_tone_check_flags_false_urgency() -> None:
    flags = spam_tone_check("Act now, this offer won't last!")
    assert any("urgency" in f for f in flags)


def test_spam_tone_check_flags_undisclosed_pitching() -> None:
    flags = spam_tone_check("Check out my new product, it's a game changer.")
    assert any("pitching" in f for f in flags)


def test_spam_tone_check_flags_fake_familiarity() -> None:
    flags = spam_tone_check("As we discussed, I'd love to follow up.")
    assert any("familiarity" in f for f in flags)


def test_spam_tone_check_flags_mass_merge_placeholder() -> None:
    flags = spam_tone_check("Hi {{first_name}}, hope you're well.")
    assert any("mass-merge" in f for f in flags)


def test_spam_tone_check_passes_clean_message() -> None:
    assert (
        spam_tone_check("Your recent post on API versioning matched a problem I hit last week.")
        == []
    )


def test_soft_cap_warning_none_under_cap() -> None:
    assert soft_cap_warning(OUTREACH_DAILY_SOFT_CAP) is None
    assert soft_cap_warning(0) is None


def test_soft_cap_warning_fires_over_cap() -> None:
    warning = soft_cap_warning(OUTREACH_DAILY_SOFT_CAP + 1)
    assert warning is not None
    assert "quality" in warning.lower()


def test_annotate_variant_adds_flags() -> None:
    variant = {"text": "Your profile is amazing, act now!"}
    annotated = annotate_variant(variant, text_field="text", context={})
    assert annotated["personalisation_flags"] == []  # no context to check against
    assert len(annotated["spam_flags"]) >= 2  # flattery + urgency


def test_annotate_variant_leaves_non_string_field_untouched() -> None:
    variant = {"text": None}
    assert annotate_variant(variant, text_field="text", context={}) == variant


def test_make_variants_postprocessor_annotates_every_variant() -> None:
    postprocess = make_variants_postprocessor(text_field="text", context_fields=["headline"])
    output = {
        "variants": [
            {"text": "Your profile is amazing!"},
            {"text": "Your work on distributed systems at Acme was a great read."},
        ]
    }
    raw_input = {"headline": "Senior Platform Engineer building distributed systems at Acme"}
    result = postprocess(output, raw_input)
    variants = result["variants"]
    assert "flattery opener detected" in variants[0]["spam_flags"]
    assert variants[0]["personalisation_flags"] != []
    assert variants[1]["personalisation_flags"] == []


def test_make_variants_postprocessor_ignores_malformed_output() -> None:
    postprocess = make_variants_postprocessor(text_field="text", context_fields=[])
    assert postprocess({"not_variants": []}, {}) == {"not_variants": []}
