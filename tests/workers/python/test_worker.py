import json
from typing import cast
from unittest.mock import AsyncMock

import pytest

from proxyflare.workers.python.worker import create_error_response, on_fetch


@pytest.mark.asyncio
async def test_on_fetch_valid_url_param(mock_env):
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com"
    request = Request(f"http://worker.dev/?url={target_url}")

    response = await on_fetch(request, mock_env)

    assert response.status == 200
    fetch_mock.assert_called_once()
    call_args = fetch_mock.call_args
    assert call_args[0][0] == target_url
    assert call_args[0][1]["method"] == "GET"


@pytest.mark.asyncio
async def test_on_fetch_missing_url(mock_env):
    from js import Request

    request = Request("http://worker.dev")
    response = await on_fetch(request, mock_env)
    assert response.status == 400

    body = json.loads(response.body)
    assert body["error"] == "Missing target URL"


@pytest.mark.asyncio
async def test_on_fetch_post_method_and_body(mock_env):
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com/api"

    # Mock request with POST and body
    request = Request(
        f"http://worker.dev/?url={target_url}",
        method="POST",
        body="test_data",
        headers={"Content-Type": "application/json"},
    )

    await on_fetch(request, mock_env)

    fetch_mock.assert_called_once()
    args = fetch_mock.call_args[0]
    target = args[0]
    opts = args[1]

    assert target == target_url
    assert opts["method"] == "POST"
    assert opts["body"] == "test_data"
    assert opts["headers"].get("content-type") == "application/json"


@pytest.mark.asyncio
async def test_on_fetch_filters_headers(mock_env):
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com"

    request = Request(
        f"http://worker.dev/?url={target_url}",
        headers={
            "X-Custom": "value",
            "Host": "worker.dev",
            "Cf-Ray": "12345",
            "User-Agent": "TestAgent",
        },
    )

    await on_fetch(request, mock_env)

    args = fetch_mock.call_args[0]
    headers = args[1]["headers"]

    assert headers.get("x-custom") == "value"
    assert headers.get("user-agent") == "TestAgent"
    assert "host" not in headers
    assert "cf-ray" not in headers
    # X-Forwarded-For is now always set (random IP if not provided)
    assert "X-Forwarded-For" in headers or "x-forwarded-for" in headers


@pytest.mark.asyncio
async def test_on_fetch_handles_exception(mock_env):
    from js import Request, fetch

    fetch_mock = cast(AsyncMock, fetch)
    # Mock fetch raising an exception
    fetch_mock.side_effect = Exception("Network Error")

    target_url = "https://example.com"
    request = Request(f"http://worker.dev/?url={target_url}")

    response = await on_fetch(request, mock_env)

    assert response.status == 502

    body = json.loads(response.body)
    assert "error" in body
    assert "Proxy Error" in body["error"]


@pytest.mark.asyncio
async def test_on_fetch_empty_url_param(mock_env):
    from js import Request

    # Test with ?url= (empty value)
    request = Request("http://worker.dev/?url=")
    response = await on_fetch(request, mock_env)
    assert response.status == 400

    body = json.loads(response.body)
    assert body["error"] == "Missing target URL"


@pytest.mark.asyncio
async def test_options_cors(mock_env):
    from js import Request

    request = Request("http://worker.dev/", method="OPTIONS")
    response = await on_fetch(request, mock_env)

    assert response.status == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "*"
    assert "GET, POST" in response.headers.get("Access-Control-Allow-Methods")


@pytest.mark.asyncio
async def test_target_url_from_header(mock_env):
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com/header"

    request = Request("http://worker.dev/", headers={"X-Target-URL": target_url})

    await on_fetch(request, mock_env)

    fetch_mock.assert_called_once()
    assert fetch_mock.call_args[0][0] == target_url


@pytest.mark.asyncio
async def test_target_url_from_path(mock_env):
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com/path"

    # Path: /https://example.com/path
    request = Request(f"http://worker.dev/{target_url}")

    await on_fetch(request, mock_env)

    fetch_mock.assert_called_once()
    assert fetch_mock.call_args[0][0] == target_url


@pytest.mark.asyncio
async def test_x_forwarded_for_random_ip(mock_env):
    """X-Forwarded-For should be set with a random IP when not provided."""
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com"
    request = Request(f"http://worker.dev/?url={target_url}")

    await on_fetch(request, mock_env)

    args = fetch_mock.call_args[0]
    headers = args[1]["headers"]
    forwarded = headers.get("X-Forwarded-For")
    assert forwarded is not None
    # Should be a valid IP-like format (4 octets)
    octets = forwarded.split(".")
    assert len(octets) == 4
    for octet in octets:
        assert 1 <= int(octet) <= 255


@pytest.mark.asyncio
async def test_x_forwarded_for_custom_header(mock_env):
    """X-My-X-Forwarded-For should be passed as X-Forwarded-For."""
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com"
    request = Request(
        f"http://worker.dev/?url={target_url}",
        headers={"X-My-X-Forwarded-For": "1.2.3.4"},
    )

    await on_fetch(request, mock_env)

    args = fetch_mock.call_args[0]
    headers = args[1]["headers"]
    assert headers.get("X-Forwarded-For") == "1.2.3.4"
    # x-my-x-forwarded-for should NOT be passed through
    assert "x-my-x-forwarded-for" not in headers


@pytest.mark.asyncio
async def test_filters_cb_and_t_params(mock_env):
    """_cb and _t cache-buster params should be stripped from the target URL."""
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com/api?key=value"
    request = Request(f"http://worker.dev/?url={target_url}&_cb=123&_t=456&extra=yes")

    await on_fetch(request, mock_env)

    fetch_mock.assert_called_once()
    proxied_url = fetch_mock.call_args[0][0]
    # key=value and extra=yes should remain, _cb and _t should be filtered
    assert "key=value" in proxied_url
    assert "extra=yes" in proxied_url
    assert "_cb" not in proxied_url
    assert "_cb" not in proxied_url
    assert "_t" not in proxied_url


@pytest.mark.asyncio
async def test_header_duplication_repro(mock_env):
    """
    Test if X-Forwarded-For mock is duplicated if existing header is lowercase
    and logic uses CamelCase check.
    """
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    fetch_mock.return_value = Response("OK")
    target_url = "https://example.com"

    # Existing x-forwarded-for (lowcase)
    # The fix ensures we don't add a RANDOM one if this exists.
    request = Request(
        f"http://worker.dev/?url={target_url}", headers={"x-forwarded-for": "203.0.113.1"}
    )

    await on_fetch(request, mock_env)

    call_args = fetch_mock.call_args
    headers = call_args[0][1]["headers"]

    # Verify we didn't add a second X-Forwarded-For
    keys = [k for k in headers.keys() if k.lower() == "x-forwarded-for"]
    assert len(keys) == 1
    assert headers[keys[0]] == "203.0.113.1"


@pytest.mark.asyncio
async def test_response_header_filtering(mock_env):
    """Test that content-encoding etc are filtered from response."""
    from js import Request, Response, fetch

    fetch_mock = cast(AsyncMock, fetch)
    # Mock response WITH headers that should be filtered
    fetch_mock.return_value = Response(
        "OK",
        {
            "headers": {
                "Content-Encoding": "gzip",
                "Content-Length": "123",
                "Transfer-Encoding": "chunked",
                "X-Keep-This": "true",
            }
        },
    )

    request = Request("http://worker.dev/?url=https://example.com")
    response = await on_fetch(request, mock_env)

    assert response.status == 200

    headers = response.headers
    assert "content-encoding" not in headers
    assert "content-length" not in headers
    assert "transfer-encoding" not in headers
    assert "x-keep-this" in headers


@pytest.mark.asyncio
async def test_create_error_response_cors_headers():
    """Test unused branch in create_error_response."""

    custom_cors = {"Access-Control-Allow-Origin": "example.com"}
    resp = create_error_response("Err", cors_headers=custom_cors)

    headers = resp.headers
    assert headers.get("access-control-allow-origin") == "example.com"
