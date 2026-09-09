#!/usr/bin/env python3
"""Installation script for GitLab CLI"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import ensure_package, info, parse_dry_run


def main():
    parse_dry_run()
    info("Installing GitLab CLI...")

    if not ensure_package(
        'GitLab CLI', brew='glab', pacman='glab', mise='glab', command='glab'
    ):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
