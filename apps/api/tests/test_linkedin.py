from httpx import AsyncClient


async def test_linkedin_start_without_configuration_fails_cleanly(
    client: AsyncClient,
) -> None:
    # No LINKEDIN_CLIENT_ID/SECRET is configured in the test environment;
    # the endpoint must fail loudly rather than build a broken URL.
    response = await client.get("/api/v1/auth/linkedin/start")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL"
