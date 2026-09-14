from __future__ import annotations

from app.audit.scoring import component_weight, load_scoring_config, weighted_average


def test_scoring_config_loads_and_validates_weights() -> None:
    config = load_scoring_config()
    assert config.scoring_version
    assert sum(config.category_weights.values()) == 100
    for category, components in config.category_components.items():
        assert sum(c.weight for c in components) == 100, category


def test_all_five_categories_are_configured() -> None:
    config = load_scoring_config()
    assert set(config.category_weights) == {
        "profile",
        "content",
        "engagement",
        "career",
        "visibility",
    }


def test_component_weight_looks_up_by_code() -> None:
    weight = component_weight("profile", "completeness")
    assert isinstance(weight, int)
    assert weight > 0


def test_weighted_average_basic() -> None:
    result = weighted_average({"a": 100, "b": 0}, {"a": 50, "b": 50})
    assert result == 50


def test_weighted_average_renormalizes_missing_components() -> None:
    # "b" unavailable -- "a" alone should carry the full weight, not be
    # diluted as if "b" contributed a zero.
    result = weighted_average({"a": 80, "b": None}, {"a": 30, "b": 70})
    assert result == 80


def test_weighted_average_returns_none_when_nothing_available() -> None:
    assert weighted_average({"a": None, "b": None}, {"a": 50, "b": 50}) is None
