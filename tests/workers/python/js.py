from unittest.mock import MagicMock

# This file exists to satisfy linters and local imports during testing.
# The actual mocking is handled in conftest.py via sys.modules.


class Headers(MagicMock):
    pass


class Request(MagicMock):
    pass


class Response(MagicMock):
    pass


class Object(MagicMock):
    pass


def fetch(*args, **kwargs):
    pass
