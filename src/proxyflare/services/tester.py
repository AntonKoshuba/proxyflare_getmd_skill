import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed

from proxyflare.constants import DEFAULT_WORKER_TIMEOUT, DEFAULT_WORKER_WAIT

__all__ = ["WorkerTester"]


class WorkerTester:
    """Service for testing deploed Cloudflare Workers."""

    def __init__(self, timeout: float = DEFAULT_WORKER_TIMEOUT) -> None:
        """
        Initialize the WorkerTester.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(DEFAULT_WORKER_WAIT))
    def check_health(self, url: str) -> bool:
        """
        Check if the worker is reachable and responding.

        Args:
            url: The public URL of the worker to check.

        Returns:
            True if reachable, False otherwise.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                client.get(url)
                return True
        except Exception as e:
            logger.debug(f"Health check failed for {url}: {e}")
            return False

    def test_proxy(self, worker_url: str, target_url: str) -> bool:
        """
        Verify that the worker correctly proxies a request to the target URL.

        Args:
            worker_url: The public URL of the worker.
            target_url: The URL to proxy to.

        Returns:
            True if the proxy request was successful (200 OK), False otherwise.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                # Construct proxy URL: worker_url/?url=target_url
                resp = client.get(f"{worker_url}", params={"url": target_url})
                if resp.status_code == 200:
                    return True
                logger.warning(f"Proxy test returned {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"Proxy test failed: {e}")
            return False
