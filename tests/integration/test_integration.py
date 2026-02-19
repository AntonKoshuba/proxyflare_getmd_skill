import httpx
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worker_health_check(worker_base_url: str):
    """Verify the worker is reachable."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{worker_base_url}/?url=https://httpbin.org/get")
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://httpbin.org/get"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worker_post_proxy(worker_base_url: str):
    """Verify POST request proxying."""
    async with httpx.AsyncClient() as client:
        payload = {"test": "data"}
        response = await client.post(
            f"{worker_base_url}/?url=https://httpbin.org/post", json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["json"] == payload
        assert data["headers"]["Content-Type"] == "application/json"
