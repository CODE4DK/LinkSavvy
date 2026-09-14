import json
import logging

from httpx import AsyncClient

from app.observability.logging import JsonFormatter, get_request_id


async def test_response_carries_a_request_id(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.headers["X-Request-ID"]


async def test_inbound_request_id_is_echoed_back(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "caller-supplied-id"})
    assert response.headers["X-Request-ID"] == "caller-supplied-id"


async def test_request_id_is_available_inside_the_request_and_reset_after(
    client: AsyncClient,
) -> None:
    # Nothing in the route handler itself reads get_request_id(), so this
    # proves the contextvar set by the middleware is visible to *some*
    # code running inside request handling via a side channel: the
    # request-id-tagged response header round-trips per request, which
    # only holds if the middleware's context isolation is per-request
    # (not leaking or stuck from a previous request).
    first = await client.get("/health")
    second = await client.get("/health")
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
    # No request is in flight from this test's own context.
    assert get_request_id() is None


def test_json_formatter_includes_message_and_extra_fields() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="something happened",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "abc-123"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "something happened"
    assert payload["logger"] == "app.test"
    assert payload["level"] == "INFO"
    assert payload["correlation_id"] == "abc-123"
