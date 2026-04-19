#!/usr/bin/env python3
"""Install Rust toolchain via mise."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import command_exists, error, info, mise_use, parse_dry_run, success


def main():
    parse_dry_run()
    info("Installing Rust via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    if not mise_use('rust@latest'):
        error("Failed to install Rust via mise")
        return 1

    success("Rust installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
