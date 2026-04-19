#!/usr/bin/env python3
"""Installation script for fnox (1Password secret injection via mise)

Installed via `mise use -g cargo:fnox` per the mise-adoption spec
(requires a Rust toolchain, which the `rust` topic installs via mise).
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists


def _mise_run(args):
    """Run a mise command, inheriting stdout/stderr."""
    return subprocess.run(['mise', *args], check=True)


def main():
    info("Installing fnox...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    if command_exists('fnox'):
        success("fnox already installed")
        return 0

    try:
        _mise_run(['use', '-g', 'cargo:fnox'])
    except subprocess.CalledProcessError:
        error("Failed to install fnox via 'mise use -g cargo:fnox'")
        return 1

    success("fnox installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
