import asyncio

from rich.table import Table

from proxyflare.cli.console import console
from proxyflare.cli.context import get_app_context
from proxyflare.cli.exceptions import APIError


async def _list_workers_async() -> None:
    """Asynchronous implementation of the worker list command."""
    async with get_app_context() as ctx:
        try:
            workers = await ctx.service.list_workers()
        except Exception as e:
            raise APIError(
                "Failed to list workers. Check your API token and network connection."
            ) from e

        if not workers:
            console.print("[yellow]No workers found.[/yellow]")
            return

        table = Table(title="Deployed Workers")
        table.add_column("Name", style="cyan")
        table.add_column("Created On", style="magenta")
        table.add_column("Modified On", style="green")

        for worker in workers:
            created_on = worker.get("created_on")
            modified_on = worker.get("modified_on")

            # Convert datetime objects to string if they exist
            if created_on and not isinstance(created_on, str):
                created_on = created_on.isoformat()
            if modified_on and not isinstance(modified_on, str):
                modified_on = modified_on.isoformat()

            table.add_row(worker.get("id", "Unknown"), created_on or "N/A", modified_on or "N/A")

        console.print(table)


def list_workers() -> None:
    """Display all active proxy workers."""
    asyncio.run(_list_workers_async())
