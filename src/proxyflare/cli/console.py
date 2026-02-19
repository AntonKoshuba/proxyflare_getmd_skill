from rich.console import Console

__all__ = [
    "console",
    "err_console",
    "print_error",
    "print_info",
    "print_success",
    "print_warning",
]

# Global console instances using rich defaults
# standard console for stdout
console = Console()
"""Standard console for stdout."""

# error console for stderr
err_console = Console(stderr=True)
"""Error console for stderr."""


def print_error(message: str) -> None:
    """Print an error message to stderr with consistent styling."""
    err_console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message to stdout with consistent styling."""
    console.print(f"[bold green]{message}[/bold green]")


def print_warning(message: str) -> None:
    """Print a warning message to stderr with consistent styling."""
    err_console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message to stdout."""
    console.print(f"[blue]{message}[/blue]")
