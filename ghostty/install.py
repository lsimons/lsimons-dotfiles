#!/usr/bin/env python3
"""Installation script for Ghostty terminal"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import ensure_package, info, install_symlinks, parse_dry_run


def main():
    parse_dry_run()
    info("Installing Ghostty...")

    # Optional on Linux: Arch ships ghostty in extra for x86_64 only, and
    # building ghostty-git from source is not something an idempotent
    # dotfiles run should do unattended. Omarchy's own terminal (foot)
    # stays the default there; the config symlinks below are installed
    # either way so Ghostty is themed if it does turn up.
    if not ensure_package(
        'Ghostty',
        brew='ghostty',
        cask=True,
        macos_app='Ghostty',
        pacman='ghostty',
        command='ghostty',
        optional=True,
    ):
        return 1

    if not install_symlinks(Path(__file__).resolve().parent):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
