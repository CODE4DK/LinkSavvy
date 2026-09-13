from __future__ import annotations

from app.workspace.search import boolean_mode_query


def test_boolean_mode_query_requires_a_prefix_match_on_every_word() -> None:
    assert boolean_mode_query("backend reliability") == "+backend* +reliability*"


def test_boolean_mode_query_strips_punctuation() -> None:
    assert boolean_mode_query("on-call, ownership!") == "+on-call* +ownership*"


def test_boolean_mode_query_handles_a_single_word() -> None:
    assert boolean_mode_query("headline") == "+headline*"
