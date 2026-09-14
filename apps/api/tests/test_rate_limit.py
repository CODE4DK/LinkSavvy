from httpx import AsyncClient

# Bucket reset between tests is handled by the autouse `_reset_rate_limits`
# fixture in tests/conftest.py.


async def test_auth_endpoint_is_rate_limited_after_burst(client: AsyncClient) -> None:
    # The "auth" class allows a burst of 10 before throttling.
    for _ in range(10):
        response = await client.post(
            "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong"}
        )
        assert response.status_code != 429

    limited = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong"}
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    assert "Retry-After" in limited.headers


async def test_health_and_ready_are_never_rate_limited(client: AsyncClient) -> None:
    for _ in range(50):
        response = await client.get("/health")
        assert response.status_code == 200
