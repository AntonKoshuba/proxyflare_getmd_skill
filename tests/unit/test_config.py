import pytest
from pydantic import ValidationError

from proxyflare.models.config import Config


def test_config_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("PROXYFLARE_ACCOUNT_ID", "env_account")
    monkeypatch.setenv("PROXYFLARE_API_TOKEN", "env_token")

    config = Config(_env_file=None)  # type: ignore[call-arg]
    assert config.account_id == "env_account"
    assert config.api_token.get_secret_value() == "env_token"


def test_config_missing_env(monkeypatch):
    """Test that Config raises ValidationError if required vars are missing."""
    monkeypatch.delenv("PROXYFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("PROXYFLARE_API_TOKEN", raising=False)

    with pytest.raises(ValidationError):
        Config(_env_file=None)  # type: ignore[call-arg]
