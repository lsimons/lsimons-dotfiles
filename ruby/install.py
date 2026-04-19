#!/usr/bin/env python3
"""Install Ruby via mise."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import command_exists, error, info, mise_use, parse_dry_run, success


def main():
    parse_dry_run()
    info("Installing Ruby via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    if not mise_use('ruby@3.4'):
        error("Failed to install Ruby via mise")
        return 1

    success("Ruby installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
