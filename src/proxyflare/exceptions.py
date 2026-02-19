__all__ = ["ProxyflareError", "SubdomainMissingError"]


class ProxyflareError(Exception):
    """Base exception for all Proxyflare errors."""


class SubdomainMissingError(ProxyflareError):
    """Raised when the Cloudflare account has no subdomain configured."""
