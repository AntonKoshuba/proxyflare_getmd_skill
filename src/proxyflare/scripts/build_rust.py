#!/usr/bin/env python3
"""
Script to build Rust workers for Proxyflare.
Wraps 'cargo install -q worker-build && worker-build --release'
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    rust_dir = Path(__file__).parent.parent / "workers" / "rust"

    if not rust_dir.exists():
        print(f"Error: Rust worker directory not found at {rust_dir}")
        sys.exit(1)

    try:
        # Locate worker-build executable or install it
        worker_build_cmd = "worker-build"
        cargo_home = Path.home() / ".cargo"
        potential_bin = cargo_home / "bin" / "worker-build"

        if not shutil.which(worker_build_cmd) and not potential_bin.exists():
            print("Installing 'worker-build' tool...")
            try:
                subprocess.run(["cargo", "install", "-q", "worker-build"], check=True)  # noqa: S607
            except subprocess.CalledProcessError as e:
                print(f"\nError: Failed to install 'worker-build' via cargo: {e}")
                print("\nThis usually happens due to:")
                print("1. Missing network connection.")
                print("2. Cargo/Rust not being installed or not in PATH.")
                print("3. Permission issues.")
                print("\nPlease ensure Rust is installed (https://rustup.rs/) and try again.")
                sys.exit(1)

        if not shutil.which(worker_build_cmd) and potential_bin.exists():
            worker_build_cmd = str(potential_bin)

        print(f"Running build with {worker_build_cmd}...")
        subprocess.run([worker_build_cmd, "--release"], cwd=rust_dir, check=True)

        print("Build successful!")

    except subprocess.CalledProcessError as e:
        print(f"\nError building Rust worker: {e}")
        print("\nPossible solutions:")
        print("1. Ensure Rust and Cargo are installed.")
        print("2. Ensure you have network access for 'cargo install'.")
        print("3. Check for compilation errors in the Rust code.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
