#!/usr/bin/env python3
"""Installation script for topgrade (automated system updater)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import ensure_package, info, install_symlinks, parse_dry_run


def main():
    parse_dry_run()
    info("Installing topgrade...")

    # No Arch repo carries topgrade; it is an AUR build.
    if not ensure_package(
        'topgrade', brew='topgrade', aur='topgrade', mise='topgrade', command='topgrade'
    ):
        return 1

    if not install_symlinks(Path(__file__).resolve().parent):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
