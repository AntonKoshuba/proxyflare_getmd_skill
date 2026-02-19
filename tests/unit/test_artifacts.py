from unittest.mock import MagicMock, patch

import pytest

from proxyflare.utils.artifacts import build_rust_worker


@pytest.fixture
def mock_path():
    with patch("proxyflare.utils.artifacts.Path") as MockPath:
        yield MockPath


@pytest.fixture
def mock_shutil():
    with patch("proxyflare.utils.artifacts.shutil") as MockShutil:
        yield MockShutil


@pytest.fixture
def mock_subprocess():
    with patch("proxyflare.utils.artifacts.subprocess.run") as MockRun:
        yield MockRun


def test_build_rust_worker_success(mock_shutil, mock_subprocess):
    # Mock cargo existence
    mock_shutil.which.return_value = "/usr/bin/cargo"

    # Mock script path existence
    with patch("proxyflare.utils.artifacts.Path") as MockPath:
        mock_root = MagicMock()
        MockPath.return_value.parent.parent = mock_root
        mock_script = mock_root.joinpath.return_value.joinpath.return_value
        mock_script.exists.return_value = True

        # Run
        result = build_rust_worker(verbose=False)

        assert result is True
        mock_subprocess.assert_called_once()


def test_build_rust_worker_no_cargo(mock_shutil):
    mock_shutil.which.return_value = None

    result = build_rust_worker(verbose=False)
    assert result is False


def test_build_rust_worker_no_script(mock_shutil, mock_subprocess):
    mock_shutil.which.return_value = "/usr/bin/cargo"
    with patch("proxyflare.utils.artifacts.Path") as MockPath:
        mock_root = MagicMock()
        MockPath.return_value.parent.parent = mock_root
        mock_script = mock_root.__truediv__.return_value.__truediv__.return_value
        mock_script.exists.return_value = False

        assert build_rust_worker(verbose=False) is False
        assert mock_subprocess.call_count == 0


def test_build_rust_worker_subprocess_error(mock_shutil, mock_subprocess):
    import subprocess

    mock_shutil.which.return_value = "/usr/bin/cargo"
    with patch("proxyflare.utils.artifacts.Path") as MockPath:
        mock_root = MagicMock()
        MockPath.return_value.parent.parent = mock_root
        mock_script = mock_root.__truediv__.return_value.__truediv__.return_value
        mock_script.exists.return_value = True

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")

        assert build_rust_worker(verbose=False) is False
