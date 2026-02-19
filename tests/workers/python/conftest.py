import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Mock the 'js' module which is available in Cloudflare Workers
mock_js = MagicMock()
mock_js.fetch = AsyncMock()
sys.modules["js"] = mock_js

# Mock 'pyodide' module
mock_pyodide = MagicMock()
mock_ffi = MagicMock()
mock_pyodide.ffi = mock_ffi


def to_js_mock(obj, **kwargs):
    return obj


mock_ffi.to_js = to_js_mock
sys.modules["pyodide"] = mock_pyodide
sys.modules["pyodide.ffi"] = mock_ffi


class MockHeaders(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if args:
            for k, v in args[0].items():
                self[k.lower()] = v
        for k, v in kwargs.items():
            self[k.lower()] = v

    def get(self, key, default=None):
        return super().get(key.lower(), default)

    def set(self, key, value):
        self[key.lower()] = value

    def entries(self):
        return self.items()


class MockRequest:
    def __init__(self, url, method="GET", headers=None, body=None):
        self.url = url
        self.method = method
        self.headers = MockHeaders(headers or {})
        self.body = body

    @classmethod
    def new(cls, *args, **kwargs):
        return cls(*args, **kwargs)


class MockResponse:
    def __init__(self, body=None, status=200, headers=None, statusText="OK"):
        # Handle JS-style new Response(body, init) signature where init is a dict.
        # (passed as 'status' arg here if positional).
        # OR if passed as kwargs, logic below handles it.
        # But commonly in our new worker.py: Response.new(body, init_js)
        # -> init_js is passed as 2nd arg 'status'

        if isinstance(status, dict):
            init = status
            self.body = body
            self.status = init.get("status", 200)
            self.statusText = init.get("statusText", "OK")
            self.headers = MockHeaders(init.get("headers", {}))
        else:
            self.body = body
            self.status = status
            self.statusText = statusText
            self.headers = MockHeaders(headers or {})

    @classmethod
    def new(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def json(cls, data, init=None, **kwargs):
        import json

        # If data is already a string, assume it's JSON encoded
        if isinstance(data, str):
            body = data
        else:
            body = json.dumps(data)

        # Handle JS-style Response.json(data, init)
        # Verify if 'init' is passed as 2nd arg. In python signature above 'init' captures it.

        status = 200
        headers = None
        statusText = "OK"

        if init and isinstance(init, dict):
            status = init.get("status", 200)
            headers = init.get("headers")
            statusText = init.get("statusText", "OK")
        else:
            # Fallback for legacy calls matching json(data, status=..., headers=...)
            # If 'init' was passed as status (int), it's handled here?
            # Wait, signature is json(cls, data, init=None, **kwargs).
            # If caller does json(data, 200), init=200.
            if isinstance(init, int):
                status = init
                headers = kwargs.get("headers")
            else:
                status = kwargs.get("status", 200)
                headers = kwargs.get("headers")

        return cls(body=body, status=status, headers=headers, statusText=statusText)


# Attach mock classes to the mock_js module
mock_js.Request = MockRequest
mock_js.Response = MockResponse
mock_js.Headers = MockHeaders


@pytest.fixture
def mock_env():
    return {}


@pytest.fixture(autouse=True)
def reset_mocks():
    mock_js.reset_mock()
    if hasattr(mock_js, "fetch"):
        mock_js.fetch.reset_mock()
        mock_js.fetch.side_effect = None
        mock_js.fetch.return_value = AsyncMock()
