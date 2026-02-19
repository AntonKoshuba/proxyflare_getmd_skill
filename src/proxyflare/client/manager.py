import secrets
from pathlib import Path

from proxyflare.models.worker_result import WorkerResultFile

__all__ = ["ProxyflareWorkersManager"]


class ProxyflareWorkersManager:
    """
    Manages a list of Proxyflare worker URLs.
    Can load valid workers from a JSON file (created by `proxyflare create`)
    or accept a direct list of URLs.
    """

    def __init__(self, source: str | Path | list[str]) -> None:
        """
        Initialize the manager with worker sources.

        Args:
            source: A list of URLs, a path to a JSON file, or a string path.

        Raises:
            ValueError: If no workers are found.
        """
        self.workers: list[str] = []

        if isinstance(source, list):
            self.workers = source
        else:
            self.load_from_file(source)

        if not self.workers:
            raise ValueError("No workers found in the provided source.")

    def load_from_file(self, path: str | Path) -> None:
        """Load workers from a JSON file validated by WorkerResultFile model."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Worker file not found: {file_path}")

        try:
            data = file_path.read_text(encoding="utf-8")
            result_file = WorkerResultFile.model_validate_json(data)
            self.workers = [record.url for record in result_file.root]
        except Exception as e:
            raise ValueError(f"Failed to parse worker file: {e}") from e

    def get_worker(self) -> str:
        """Return a random worker URL."""
        if not self.workers:
            raise ValueError("No workers available.")
        return secrets.choice(self.workers)
