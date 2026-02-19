import subprocess
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import (  # ty:ignore[unresolved-import]
    BuildHookInterface,
)


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        print("Running CustomBuildHook to build Rust worker...")  # noqa: T201

        # We are running during `hatch build`. We need to find `build_rust.py`.
        # When building the wheel/sdist, __file__ might be in a temp dir,
        # but usually hatch runs the hook from the project root.
        project_root = Path.cwd()
        script_path = project_root / "src" / "proxyflare" / "scripts" / "build_rust.py"

        if not script_path.exists():
            print(f"Warning: Rust build script not found at {script_path}. Skipping.")  # noqa: T201
            return

        try:
            print(f"Executing: {sys.executable} {script_path}")  # noqa: T201
            subprocess.run([sys.executable, str(script_path)], check=True, cwd=str(project_root))  # noqa: S603
            print("Build hook complete.")  # noqa: T201
        except subprocess.CalledProcessError as e:
            print(f"Error in build hook (Rust compilation failed): {e}")  # noqa: T201
            print("Please check the output above for Rust/Cargo errors.")  # noqa: T201
            print("Ensure Rust is installed (https://rustup.rs/) and you have network access.")  # noqa: T201
            raise RuntimeError("Rust worker build failed") from e
        except Exception as e:
            print(f"Unexpected error in build hook: {e}")  # noqa: T201
            raise RuntimeError("Unexpected build hook error") from e
