#!/usr/bin/env python3
"""Installation script for the micro editor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import ensure_package, info, install_symlinks, parse_dry_run


def main():
    parse_dry_run()
    topic_dir = Path(__file__).resolve().parent
    # Config first, so micro is configured even if the package step fails.
    if not install_symlinks(topic_dir):
        return 1

    info("Installing micro...")

    if not ensure_package("micro", brew="micro", pacman="micro", apt="micro", command="micro"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
