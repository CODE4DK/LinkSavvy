"""Which BillingProvider a user's checkout, and every subsequent webhook
for their subscription, goes through.

Region routing happens exactly once: `provider_name_for_new_subscription`
is only ever consulted when *creating* a subscription. Once
`Subscription.provider` is set, every later operation (cancel, change
plan, the webhook lookup) reads the provider off that column instead of
re-deriving it -- so a user's billing country changing later never
migrates them between providers mid-subscription (see
app/models/user.py::billing_country and docs/adr/0011).
"""

from __future__ import annotations

from functools import lru_cache

from app.billing.providers.base import BillingProvider
from app.billing.providers.fake import FakeProvider
from app.billing.providers.razorpay import RazorpayProvider
from app.billing.providers.stripe import StripeProvider
from app.settings import settings

_PROVIDER_CLASSES: dict[str, type[BillingProvider]] = {
    "stripe": StripeProvider,
    "razorpay": RazorpayProvider,
    "fake": FakeProvider,
}


def provider_name_for_billing_country(billing_country: str | None) -> str:
    if billing_country and billing_country.upper() in settings.razorpay_billing_countries:
        return "razorpay"
    return "stripe"


@lru_cache(maxsize=8)
def _build(provider_name: str) -> BillingProvider:
    # Real classes by default; tests monkeypatch this dict itself (the
    # same pattern as app/ai/providers/registry.py's _PROVIDER_CLASSES)
    # so this function never has to know it's running under test.
    return _PROVIDER_CLASSES[provider_name]()


def get_provider(provider_name: str) -> BillingProvider:
    return _build(provider_name)
