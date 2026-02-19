from pydantic import BaseModel

from proxyflare.constants import WorkerType

__all__ = ["DeploymentConfig"]


class DeploymentConfig(BaseModel):
    """Configuration for deploying a worker."""

    name: str
    script_content: str
    worker_type: WorkerType
    wasm_content: bytes | None = None
