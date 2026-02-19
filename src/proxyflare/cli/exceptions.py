__all__ = [
    "APIError",
    "BuildError",
    "ConfigError",
    "ProxyflareError",
    "WorkerError",
]


class ProxyflareError(Exception):
    """Base exception for all Proxyflare errors."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class ConfigError(ProxyflareError):
    """Raised when there is a configuration error."""


class WorkerError(ProxyflareError):
    """Raised when a worker operation fails."""


class BuildError(ProxyflareError):
    """Raised when a worker build fails."""


class APIError(ProxyflareError):
    """Raised when an external API call fails."""
