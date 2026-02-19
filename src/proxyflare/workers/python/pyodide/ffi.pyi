"""Type stubs for pyodide.ffi module.

These stubs allow the astral/ty type checker to validate the Python worker
code without requiring the actual Pyodide runtime.
"""

from collections.abc import Callable
from typing import Any

def to_js(obj: Any, dict_converter: Callable[..., Any] | None = None) -> Any: ...
