from pydantic import ValidationError
from rich.console import Console

__all__ = ["handle_validation_error"]


def handle_validation_error(e: ValidationError) -> None:
    console = Console(stderr=True)
    console.print("[bold red]Configuration Error:[/bold red]")
    for error in e.errors():
        field_name = ".".join(str(loc) for loc in error["loc"]) or "Global Config"
        message = error["msg"]
        input_value = error.get("input")
        console.print(
            f"  Field [bold]{field_name}[/bold]: {message} "
            f"(Invalid Value: [red]{input_value!r}[/red])"
        )
