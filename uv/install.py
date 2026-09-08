#!/usr/bin/env python3
"""Installation script for uv (Python package manager)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import ensure_package, info, parse_dry_run


def main():
    parse_dry_run()
    info("Installing uv...")

    if not ensure_package('uv', brew='uv', pacman='uv', command='uv'):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
