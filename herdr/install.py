#!/usr/bin/env python3
"""Installation script for herdr (https://herdr.dev), a terminal agent multiplexer"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import ensure_package, info, install_symlinks, parse_dry_run


def main():
    parse_dry_run()
    info("Installing herdr...")

    # Omarchy ships herdr in its own pacman repo, prebuilt for aarch64.
    if not ensure_package('herdr', brew='herdr', pacman='herdr', command='herdr'):
        return 1

    if not install_symlinks(Path(__file__).resolve().parent):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
