from __future__ import annotations

from app.ai.redact import redact_mapping, redact_text


def test_redact_text_never_returns_the_value() -> None:
    value = "some sensitive user content"
    result = redact_text(value)
    assert "sensitive" not in result
    assert str(len(value)) in result  # the length is the only thing revealed


def test_redact_mapping_redacts_text_bearing_keys() -> None:
    result = redact_mapping({"message": "secret text", "user_id": "abc-123", "count": 3})
    assert result["message"] != "secret text"
    assert "secret text" not in str(result)
    assert result["user_id"] == "abc-123"
    assert result["count"] == 3


def test_redact_mapping_recurses_into_nested_mappings() -> None:
    result = redact_mapping({"outer": {"content": "hidden", "id": 1}})
    assert "hidden" not in str(result)
    assert result["outer"]["id"] == 1


def test_redact_mapping_recurses_into_lists_of_mappings() -> None:
    result = redact_mapping({"items": [{"text": "one"}, {"text": "two"}]})
    assert "one" not in str(result)
    assert "two" not in str(result)


def test_redact_mapping_is_case_insensitive_on_keys() -> None:
    result = redact_mapping({"Message": "secret"})
    assert "secret" not in str(result)
