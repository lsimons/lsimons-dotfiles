#!/usr/bin/env python3
"""Installation script for Vivaldi Browser"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import ensure_package, info, parse_dry_run


def main():
    parse_dry_run()
    info("Installing Vivaldi Browser...")

    # Optional on Linux: Vivaldi ships x86_64 binaries only, so the AUR
    # package has nothing to install from on aarch64 (where Omarchy
    # provides omarchy-chromium instead). A missing browser should not
    # fail the whole run.
    if not ensure_package(
        'Vivaldi Browser',
        brew='vivaldi',
        cask=True,
        macos_app='Vivaldi',
        pacman='vivaldi',
        command='vivaldi',
        optional=True,
    ):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
