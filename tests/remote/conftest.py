import uuid
from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
from cloudflare import AsyncCloudflare
from rich.console import Console
from tenacity import retry, stop_after_delay, wait_exponential

from proxyflare.models.config import Config
from proxyflare.models.deployment import DeploymentConfig
from proxyflare.services.worker import WorkerService

console = Console()


@retry(stop=stop_after_delay(60), wait=wait_exponential(multiplier=1, min=4, max=10))
async def wait_for_worker(url: str) -> None:
    """Poll the worker until it returns 200 or 400 (bad request is ok for root)."""
    async with httpx.AsyncClient() as client:
        try:
            # We filter for query param 'url', so a raw GET should return 400 if working
            # or 200 if the worker logic permits.
            # 404 means it's not propagated yet.
            response = await client.get(url)
            if response.status_code not in (200, 400):
                raise RuntimeError(f"Worker not ready: {response.status_code}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Worker not reachable: {e}") from e


@pytest.fixture(scope="session")
def config() -> Config:
    """Yields a loaded Config object."""
    try:
        return Config()  # type: ignore
    except Exception as e:
        pytest.skip(f"Configuration not valid: {e}")


@pytest.fixture(scope="session")
def cloudflare_client(config: Config) -> Generator[AsyncCloudflare, None, None]:
    """Yields an authenticated Cloudflare client."""
    yield AsyncCloudflare(api_token=config.api_token.get_secret_value())


@pytest.fixture(scope="session")
def worker_service(
    cloudflare_client: AsyncCloudflare, config: Config
) -> Generator[WorkerService, None, None]:
    """Yields a WorkerService instance."""
    yield WorkerService(client=cloudflare_client, account_id=config.account_id)


@pytest.fixture(scope="session")
async def worker_base_url(worker_service: WorkerService) -> AsyncGenerator[str, None]:
    """
    Fixture that:
    1. Deploys a worker using WorkerService.
    2. Yields the URL.
    3. Deletes the worker after tests.
    """
    # Generate a unique name
    unique_id = uuid.uuid4().hex[:8]
    worker_name = f"proxyflare-e2e-test-{unique_id}"

    console.print(f"\n[bold blue]Deploying test worker: {worker_name}[/bold blue]")

    # Ensure rust artifacts are built before attempting to deploy
    from proxyflare.utils.artifacts import build_rust_worker

    build_rust_worker(verbose=False)

    # Get worker source
    script_content, wasm_content = worker_service.get_worker_source("rust")

    config = DeploymentConfig(
        name=worker_name,
        script_content=script_content,
        worker_type="rust",
        wasm_content=wasm_content,
    )

    try:
        url = await worker_service.deploy_worker(config)
        console.print(f"[bold green]Worker deployed at: {url}[/bold green]")

        console.print("[bold blue]Waiting for propagation...[/bold blue]")
        await wait_for_worker(url)
        console.print("[bold green]Worker is ready![/bold green]")

        yield url

    finally:
        try:
            await worker_service.delete_worker(worker_name)
        except Exception as e:
            console.print(f"[bold red]Failed to delete worker {worker_name}: {e}[/bold red]")
