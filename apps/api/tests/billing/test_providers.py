from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from app.billing.providers.base import BillingProviderError
from app.billing.providers.razorpay import _verify_razorpay_signature
from app.billing.providers.registry import provider_name_for_billing_country
from app.billing.providers.stripe import _verify_stripe_signature


def test_region_routing_sends_india_to_razorpay() -> None:
    assert provider_name_for_billing_country("IN") == "razorpay"
    assert provider_name_for_billing_country("in") == "razorpay"


def test_region_routing_defaults_everyone_else_to_stripe() -> None:
    assert provider_name_for_billing_country("US") == "stripe"
    assert provider_name_for_billing_country(None) == "stripe"
    assert provider_name_for_billing_country("GB") == "stripe"


def test_stripe_signature_accepts_a_correctly_signed_payload() -> None:
    secret = "whsec_test"
    body = json.dumps({"id": "evt_1"}).encode()
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{body.decode()}".encode()
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"

    _verify_stripe_signature(header, body, secret)  # does not raise


def test_stripe_signature_rejects_a_tampered_payload() -> None:
    secret = "whsec_test"
    body = json.dumps({"id": "evt_1"}).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), f"{timestamp}.wrong".encode(), hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"

    with pytest.raises(BillingProviderError, match="mismatch"):
        _verify_stripe_signature(header, body, secret)


def test_stripe_signature_rejects_a_stale_timestamp() -> None:
    secret = "whsec_test"
    body = b"{}"
    timestamp = str(int(time.time()) - 10_000)
    signed_payload = f"{timestamp}.{body.decode()}".encode()
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"

    with pytest.raises(BillingProviderError, match="tolerance"):
        _verify_stripe_signature(header, body, secret)


def test_razorpay_signature_accepts_a_correctly_signed_payload() -> None:
    secret = "razorpay_test_secret"
    body = json.dumps({"event": "subscription.activated"}).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    _verify_razorpay_signature(signature, body, secret)  # does not raise


def test_razorpay_signature_rejects_a_tampered_payload() -> None:
    secret = "razorpay_test_secret"
    body = json.dumps({"event": "subscription.activated"}).encode()
    signature = hmac.new(secret.encode(), b"different body", hashlib.sha256).hexdigest()

    with pytest.raises(BillingProviderError, match="mismatch"):
        _verify_razorpay_signature(signature, body, secret)


def test_razorpay_signature_rejects_a_missing_header() -> None:
    with pytest.raises(BillingProviderError, match="missing"):
        _verify_razorpay_signature("", b"{}", "secret")
