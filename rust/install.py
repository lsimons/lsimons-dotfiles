#!/usr/bin/env python3
"""Install Rust toolchain via mise."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists


def main():
    info("Installing Rust via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    try:
        subprocess.run(['mise', 'use', '-g', 'rust@latest'], check=True)
    except subprocess.CalledProcessError:
        error("Failed to install Rust via mise")
        return 1

    success("Rust installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
