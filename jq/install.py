#!/usr/bin/env python3
"""Installation script for jq."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import brew_install, brew_is_installed, error, info, parse_dry_run, success


def main():
    parse_dry_run()
    info("Installing jq...")

    if brew_is_installed("jq"):
        success("jq already installed")
        return 0
    if brew_install("jq"):
        success("jq installed")
        return 0

    error("Failed to install jq")
    return 1


if __name__ == "__main__":
    sys.exit(main())
