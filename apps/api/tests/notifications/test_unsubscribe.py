from __future__ import annotations

import uuid

import pytest

from app.notifications.unsubscribe import (
    InvalidUnsubscribeToken,
    make_unsubscribe_token,
    parse_unsubscribe_token,
)


def test_token_round_trips() -> None:
    user_id = uuid.uuid4()
    token = make_unsubscribe_token(user_id=user_id, notification_type="product.update")
    parsed_user_id, parsed_type = parse_unsubscribe_token(token)
    assert parsed_user_id == user_id
    assert parsed_type == "product.update"


def test_tampered_token_is_rejected() -> None:
    user_id = uuid.uuid4()
    token = make_unsubscribe_token(user_id=user_id, notification_type="product.update")
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(InvalidUnsubscribeToken):
        parse_unsubscribe_token(tampered)


def test_garbage_token_is_rejected() -> None:
    with pytest.raises(InvalidUnsubscribeToken):
        parse_unsubscribe_token("not-a-real-token")
