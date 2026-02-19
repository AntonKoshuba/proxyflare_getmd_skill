import json

import pytest

from proxyflare.client import ProxyflareWorkersManager


def test_manager_init_with_list():
    workers = ["https://worker1.dev", "https://worker2.dev"]
    manager = ProxyflareWorkersManager(workers)
    assert manager.workers == workers
    assert manager.get_worker() in workers


def test_manager_init_with_file(tmp_path):
    workers = [
        {"name": "w1", "url": "https://worker1.dev", "type": "python", "created_at": 1.0},
        {"name": "w2", "url": "https://worker2.dev", "type": "rust", "created_at": 2.0},
    ]
    file_path = tmp_path / "workers.json"
    file_path.write_text(json.dumps(workers), encoding="utf-8")

    manager = ProxyflareWorkersManager(file_path)
    assert len(manager.workers) == 2
    assert "https://worker1.dev" in manager.workers
    assert "https://worker2.dev" in manager.workers


def test_manager_invalid_file():
    with pytest.raises(FileNotFoundError):
        ProxyflareWorkersManager("non_existent_file.json")


def test_manager_empty_source():
    with pytest.raises(ValueError, match="No workers found"):
        ProxyflareWorkersManager([])


def test_manager_get_worker_randomness():
    workers = ["https://w1.dev", "https://w2.dev", "https://w3.dev"]
    manager = ProxyflareWorkersManager(workers)
    picked = manager.get_worker()
    assert picked in workers


def test_manager_rejects_invalid_schema(tmp_path):
    """JSON that doesn't match WorkerResultFile schema should raise ValueError."""
    bad_data = [{"url": "https://valid.dev"}]  # missing name, type, created_at
    file_path = tmp_path / "workers.json"
    file_path.write_text(json.dumps(bad_data), encoding="utf-8")

    with pytest.raises(ValueError, match="Failed to parse"):
        ProxyflareWorkersManager(file_path)


def test_manager_js_worker_type(tmp_path):
    """JS worker type should be accepted."""
    workers = [
        {"name": "js-w1", "url": "https://js.dev", "type": "js", "created_at": 3.0},
    ]
    file_path = tmp_path / "workers.json"
    file_path.write_text(json.dumps(workers), encoding="utf-8")

    manager = ProxyflareWorkersManager(file_path)
    assert manager.workers == ["https://js.dev"]
