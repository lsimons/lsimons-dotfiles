#!/usr/bin/env python3
"""Install Node.js + pnpm via mise."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists


def _mise(args):
    return subprocess.run(['mise', *args], check=True)


def main():
    info("Installing Node.js via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    try:
        _mise(['use', '-g', 'node@24'])
    except subprocess.CalledProcessError:
        error("Failed to install Node.js via mise")
        return 1

    info("Installing pnpm via mise...")
    try:
        _mise(['use', '-g', 'pnpm@latest'])
    except subprocess.CalledProcessError:
        error("Failed to install pnpm via mise")
        return 1

    success("Node.js + pnpm installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
