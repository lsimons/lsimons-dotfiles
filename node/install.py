#!/usr/bin/env python3
"""Install Node.js + pnpm via mise."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import command_exists, error, info, mise_use, parse_dry_run, success


def main():
    parse_dry_run()
    info("Installing Node.js via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    if not mise_use('node@24'):
        error("Failed to install Node.js via mise")
        return 1

    info("Installing pnpm via mise...")
    if not mise_use('pnpm@latest'):
        error("Failed to install pnpm via mise")
        return 1

    success("Node.js + pnpm installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
