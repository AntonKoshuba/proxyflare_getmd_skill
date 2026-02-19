import httpx
import pytest
import respx

from proxyflare.services.tester import WorkerTester


@pytest.fixture
def tester():
    return WorkerTester(timeout=1.0)


@respx.mock
def test_check_health_success(tester, respx_mock):
    respx_mock.get("https://worker.dev").mock(return_value=httpx.Response(200))
    assert tester.check_health("https://worker.dev") is True


@respx.mock
def test_check_health_400(tester, respx_mock):
    # We expect 400 to also be "True" in terms of "up" based on docstring
    respx_mock.get("https://worker.dev").mock(return_value=httpx.Response(400))
    assert tester.check_health("https://worker.dev") is True


@respx.mock
def test_check_health_failure(tester, respx_mock):
    respx_mock.get("https://worker.dev").mock(side_effect=httpx.ConnectError("Failed"))
    assert tester.check_health("https://worker.dev") is False


@respx.mock
def test_test_proxy_success(tester, respx_mock):
    worker_url = "https://worker.dev"
    target_url = "https://httpbin.org/ip"
    respx_mock.get(f"{worker_url}?url={target_url}").mock(
        return_value=httpx.Response(200, json={"origin": "1.2.3.4"})
    )

    assert tester.test_proxy(worker_url, target_url) is True


@respx.mock
def test_test_proxy_failure(tester, respx_mock):
    worker_url = "https://worker.dev"
    target_url = "https://httpbin.org/ip"
    respx_mock.get(f"{worker_url}?url={target_url}").mock(return_value=httpx.Response(500))

    assert tester.test_proxy(worker_url, target_url) is False


@respx.mock
def test_test_proxy_exception(tester, respx_mock):
    worker_url = "https://worker.dev"
    target_url = "https://httpbin.org/ip"
    respx_mock.get(f"{worker_url}?url={target_url}").mock(side_effect=httpx.ConnectError("Failed"))

    assert tester.test_proxy(worker_url, target_url) is False
