import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console
from typer.testing import CliRunner

from proxyflare.cli.app import app
from proxyflare.cli.exceptions import APIError

runner = CliRunner()


def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


@pytest.fixture
def mock_ctx():
    """Mock create_app_context to return a fake AppContext."""
    mock_service = MagicMock()
    mock_service.list_workers = AsyncMock()

    mock_config = MagicMock()
    mock_config.api_token.get_secret_value.return_value = "test-token"
    mock_config.account_id = "test-account-id"
    mock_config.worker_prefix = "proxyflare"

    mock_app_ctx = MagicMock()
    mock_app_ctx.config = mock_config
    mock_app_ctx.service = mock_service
    # Provide real Console instances writing to stdout (captured by CliRunner)
    mock_app_ctx.console = Console()
    mock_app_ctx.err_console = Console()

    # Mock the async context manager
    mock_cm = MagicMock()
    mock_cm.__aenter__.return_value = mock_app_ctx
    mock_cm.__aexit__.return_value = None

    with patch("proxyflare.cli.commands.list.get_app_context", return_value=mock_cm):
        yield mock_app_ctx


def test_list_workers_empty(mock_ctx):
    mock_ctx.service.list_workers.return_value = []

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "No workers found" in result.stdout
    mock_ctx.service.list_workers.assert_called_once()


def test_list_workers_success(mock_ctx):
    mock_ctx.service.list_workers.return_value = [
        {"id": "proxyflare-1", "created_on": "2024-01-01", "modified_on": "2024-01-02"},
        {"id": "proxyflare-2", "created_on": None, "modified_on": None},
    ]

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "Deployed Workers" in result.stdout
    assert "proxyflare-1" in result.stdout
    assert "proxyflare-2" in result.stdout


def test_list_workers_config_error(mock_ctx):
    """Config error is now handled by get_app_context — test via raising."""
    with patch(
        "proxyflare.cli.commands.list.get_app_context",
        side_effect=SystemExit(1),
    ):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


def test_list_workers_service_error(mock_ctx):
    mock_ctx.service.list_workers.side_effect = Exception("API Error")

    # runner bypasses main(), so exception bubbles up
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 1
    assert isinstance(result.exception, APIError)
    assert "Failed to list workers" in str(result.exception)
