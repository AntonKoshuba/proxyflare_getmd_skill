from pathlib import Path
from typing import Annotated

import httpx
import typer

from proxyflare.cli.console import console, print_error, print_success, print_warning
from proxyflare.cli.exceptions import WorkerError
from proxyflare.client import ProxyflareTransport, ProxyflareWorkersManager


def test_workers(
    url: Annotated[
        str, typer.Option("--url", "-u", help="Target URL to test")
    ] = "https://httpbin.org/ip",
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of requests to perform")] = 1,
    workers_file: Annotated[
        Path, typer.Option("--workers-file", "-f", help="Path to workers JSON file")
    ] = Path("proxyflare-workers.json"),
    timeout: Annotated[float, typer.Option("--timeout", help="Timeout for each request")] = 10.0,
) -> None:
    """
    Test the proxying capabilities of deployed workers.

    Loads workers from a JSON file and performs a series of proxied requests.
    """
    # Load Workers
    try:
        manager = ProxyflareWorkersManager(workers_file)
    except FileNotFoundError:
        print_error(f"Workers file not found: [bold]{workers_file}[/bold]")
        print_warning("Run [bold]proxyflare create[/bold] first to deploy workers.")
        raise typer.Exit(1) from None
    except Exception as e:
        raise WorkerError(f"Failed to load workers file: {e}") from e

    print_success(f"Loaded {len(manager.workers)} workers.")
    console.print(f"Testing against target: [cyan]{url}[/cyan]")

    # Initialize Client
    transport = ProxyflareTransport(manager=manager)

    with httpx.Client(transport=transport, timeout=timeout) as client:
        for i in range(limit):
            console.print(f"\n[bold]Request {i + 1}/{limit}[/bold]")
            try:
                response = client.get(url)

                # Show status
                status_style = "green" if response.is_success else "red"
                console.print(f"Status: [{status_style}]{response.status_code}[/{status_style}]")

                # Show body preview
                try:
                    data = response.json()
                    console.print(f"Response: {data}")
                except Exception:
                    console.print(f"Response: {response.text[:200]}...")

            except httpx.ConnectError:
                print_error(
                    "Could not connect to worker. Check that the worker is deployed and accessible."
                )
            except Exception as e:
                print_error(f"Request failed: {e}")

    print_success("\nTest complete.")
