#!/usr/bin/env python3
"""Installation script for uv (Python package manager)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import brew_install, command_exists, error, info, parse_dry_run, success


def main():
    parse_dry_run()
    info("Installing uv...")

    if command_exists('uv'):
        success("uv already installed")
        return 0

    if brew_install('uv'):
        success("uv installed")
        return 0

    error("Failed to install uv")
    return 1


if __name__ == '__main__':
    sys.exit(main())
