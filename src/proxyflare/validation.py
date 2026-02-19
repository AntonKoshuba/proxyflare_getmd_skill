"""Validation utilities for Cloudflare API tokens and permissions."""

from typing import Any

from cloudflare.resources.user.tokens import TokensResource
from cloudflare.types.shared import Token

__all__ = ["WORKER_PERMISSIONS", "check_token_permissions", "verify_token"]

WORKER_PERMISSIONS: tuple[str, ...] = (
    "Workers Routes Write",
    "API Tokens Read",
    "Workers Scripts Write",
    "Account Settings Read",
)


def verify_token(token_resource: TokensResource) -> str:
    """Verify that the Cloudflare API token is active."""
    verify_response: Any = token_resource.verify()
    if verify_response is None:
        raise ValueError("Token verification failed.")
    token_id = verify_response.id
    if verify_response.status != "active":
        raise ValueError(f"Token is not active. Status: {verify_response.status}")
    return token_id


def check_token_permissions(token_resource: TokensResource, token_id: str) -> None:
    """Check that the token has all required permissions."""
    token_response: Token | None = token_resource.get(token_id=token_id)
    if token_response is None or token_response.policies is None:
        raise ValueError("Token policies not found.")
    current_permissions: set[str] = set()
    for policy in token_response.policies:
        if policy.effect != "allow":
            continue
        current_permissions.update(
            permission_group.name
            for permission_group in policy.permission_groups
            if permission_group.name
        )

    missing_permissions = set(WORKER_PERMISSIONS) - current_permissions

    if missing_permissions:
        raise ValueError(f"Missing required permissions: {missing_permissions}")
