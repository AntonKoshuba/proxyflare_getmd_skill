import types
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from .manager import ProxyflareWorkersManager

__all__ = ["AsyncProxyflareTransport", "ProxyflareTransport"]


class ProxyflareTransport(httpx.BaseTransport):
    """
    Synchronous transport that routes requests through Proxyflare workers.
    """

    def __init__(
        self,
        manager: "ProxyflareWorkersManager",
        verify: bool = True,
        cert: tuple | None = None,
        http1: bool = True,
        http2: bool = False,
        limits: httpx.Limits | None = None,
        trust_env: bool = True,
        retries: int = 0,
    ) -> None:
        self.manager = manager

        if limits is None:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

        # Initialize internal transport to make the actual calls to workers
        self._pool = httpx.HTTPTransport(
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            limits=limits,
            trust_env=trust_env,
            retries=retries,
        )

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        # 1. Get a worker
        worker_url = self.manager.get_worker()

        # 2. Rewrite URL
        # The worker expects target URL as 'url' query param.
        target_url = str(request.url)

        # Parse worker URL to get scheme/host
        parsed_worker = httpx.URL(worker_url)

        # New request points to worker
        proxied_url = parsed_worker.copy_with(params={"url": target_url})

        request.url = proxied_url
        request.headers["Host"] = proxied_url.host

        return self._pool.handle_request(request)

    def close(self) -> None:
        self._pool.close()

    def __enter__(self) -> "ProxyflareTransport":
        self._pool.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        self._pool.__exit__(exc_type, exc_value, traceback)


class AsyncProxyflareTransport(httpx.AsyncBaseTransport):
    """
    Asynchronous transport that routes requests through Proxyflare workers.
    """

    def __init__(
        self,
        manager: "ProxyflareWorkersManager",
        verify: bool = True,
        cert: tuple | None = None,
        http1: bool = True,
        http2: bool = False,
        limits: httpx.Limits | None = None,
        trust_env: bool = True,
        retries: int = 0,
    ) -> None:
        self.manager = manager

        if limits is None:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

        self._pool = httpx.AsyncHTTPTransport(
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            limits=limits,
            trust_env=trust_env,
            retries=retries,
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        worker_url = self.manager.get_worker()
        target_url = str(request.url)
        parsed_worker = httpx.URL(worker_url)

        proxied_url = parsed_worker.copy_with(params={"url": target_url})

        request.url = proxied_url
        request.headers["Host"] = proxied_url.host

        return await self._pool.handle_async_request(request)

    async def aclose(self) -> None:
        await self._pool.aclose()

    async def __aenter__(self) -> "AsyncProxyflareTransport":
        await self._pool.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self._pool.__aexit__(exc_type, exc_value, traceback)
