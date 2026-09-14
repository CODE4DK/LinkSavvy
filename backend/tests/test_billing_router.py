from __future__ import annotations

from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_pricing_is_public_and_built_from_plan_limits(client: AsyncClient) -> None:
    response = await client.get("/api/v1/billing/pricing")
    assert response.status_code == 200
    body = response.json()
    plans = {row["plan"] for row in body["limits"]}
    assert plans == {"free", "pro"}


async def test_billing_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/billing/subscription")).status_code == 401
    assert (await client.post("/api/v1/billing/checkout", json={"plan": "pro"})).status_code == 401


async def test_new_user_has_a_free_subscription_by_default(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/billing/subscription", headers=headers)
    assert response.status_code == 200
    assert response.json()["plan"] == "free"


async def test_checkout_returns_a_provider_url(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/billing/checkout", headers=headers, json={"plan": "pro", "interval": "month"}
    )
    assert response.status_code == 200
    assert response.json()["checkout_url"].startswith("https://")


async def test_cancel_without_a_subscription_returns_no_active_subscription(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/billing/cancel", headers=headers, json={"at_period_end": True}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NO_ACTIVE_SUBSCRIPTION"


async def test_stripe_webhook_rejects_an_unsigned_payload(client: AsyncClient) -> None:
    response = await client.post("/api/v1/billing/webhooks/stripe", content=b'{"type": "x"}')
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "WEBHOOK_SIGNATURE_INVALID"
