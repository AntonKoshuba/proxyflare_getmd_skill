import os
import signal
import subprocess
import time
from collections.abc import Generator

import httpx
import pytest
from loguru import logger
from pydantic import SecretStr

from proxyflare.models.config import Config


@pytest.fixture
def mock_config():
    """Fixture that returns a Config object with dummy values."""
    return Config(
        account_id="test_account_id",
        api_token=SecretStr("test_api_token"),
    )


def wait_for_port(url: str, timeout: int = 30) -> bool:
    """Wait for the worker to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with httpx.Client() as client:
                try:
                    client.get(f"{url}/", timeout=1)
                    return True
                except httpx.ConnectError:
                    pass
        except Exception as e:
            logger.trace(f"Waiting for port {url}: {e}")
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def worker_base_url() -> Generator[str, None, None]:
    """
    Fixture that returns the base URL for the worker.
    If WORKER_URL is set, it returns that.
    Otherwise, it starts a local wrangler dev server and returns its URL.
    """
    # Check if a remote URL is provided
    remote_url = os.getenv("WORKER_URL")
    if remote_url:
        logger.info(f"Using remote worker at: {remote_url}")
        yield remote_url.rstrip("/")
        return

    # Start local wrangler dev server
    port = 8787
    url = f"http://localhost:{port}"
    logger.info(f"Starting local wrangler dev server at {url}...")

    # We need to run wrangler in a directory containing the worker.
    # We will use the python worker since it doesn't require compiling during tests.
    from pathlib import Path

    # conftest.py is in `tests/`, so project root is its parent
    project_root = Path(__file__).parent.parent
    py_worker_dir = project_root / "src" / "proxyflare" / "workers" / "python"

    # Wrangler CLI flags for Python are currently bugged/strict.
    # Write a temporary wrangler.toml to ensure it runs
    temp_toml = py_worker_dir / "wrangler.toml"
    toml_content = """
name = "proxyflare-python-test"
main = "worker.py"
compatibility_date = "2024-03-20"
compatibility_flags = ["python_workers"]
"""
    temp_toml.write_text(toml_content)

    # Running dev directly
    process = subprocess.Popen(
        [
            "npx",
            "wrangler",
            "dev",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        cwd=str(py_worker_dir),
        text=True,
    )

    try:
        if wait_for_port(url):
            logger.info(f"Worker ready at {url}")
            yield url
        else:
            _, stderr = process.communicate(timeout=1)
            raise RuntimeError(f"Timeout waiting for worker to start. Stderr: {stderr}")
    finally:
        logger.info("Stopping local wrangler dev server...")
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except Exception:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except Exception as e:
                logger.trace(f"Failed to kill process: {e}")

        # Cleanup temp toml
        if temp_toml.exists():
            temp_toml.unlink()
