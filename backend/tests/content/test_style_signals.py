from __future__ import annotations

import pytest

from app.content.style_signals import compute_style_signals


def test_requires_at_least_one_sample() -> None:
    with pytest.raises(ValueError):
        compute_style_signals([])


def test_counts_hashtags_and_emoji() -> None:
    signals = compute_style_signals(
        ["Loving this new project! 🚀 #buildinpublic #python", "Another day, another deploy."]
    )
    assert signals.sample_count == 2
    assert signals.hashtag_frequency == pytest.approx(1.0)
    assert signals.emoji_frequency > 0


def test_first_person_ratio_favors_first_person_writer() -> None:
    signals = compute_style_signals(
        ["I shipped a feature today. My team helped me a lot.", "We are proud of our work."]
    )
    assert signals.first_person_ratio == 1.0


def test_detects_list_usage() -> None:
    signals = compute_style_signals(
        ["Here's what I learned:\n- Ship small\n- Talk to users", "No lists in this one at all."]
    )
    assert signals.uses_lists_ratio == pytest.approx(0.5)


def test_question_rate_counted_per_post() -> None:
    signals = compute_style_signals(["Why do we do this? And why now?", "A statement post."])
    assert signals.question_rate == pytest.approx(1.0)


def test_reading_grade_is_lower_for_simpler_text() -> None:
    simple = compute_style_signals(["I like cats. Cats are fun. I have two cats."])
    complex_ = compute_style_signals(
        [
            "The multidisciplinary implementation necessitates comprehensive "
            "reconsideration of foundational architectural assumptions."
        ]
    )
    assert simple.avg_reading_grade < complex_.avg_reading_grade


def test_to_context_block_includes_every_signal_label() -> None:
    signals = compute_style_signals(["A short post about mentoring engineers on my team."])
    block = signals.to_context_block()
    for label in (
        "Sample size",
        "Average sentence length",
        "Average paragraph length",
        "Line-break density",
        "Emoji frequency",
        "Hashtag frequency",
        "First-person pronoun share",
        "Questions per post",
        "Uses a bullet or numbered list",
        "Approximate reading grade level",
    ):
        assert label in block
