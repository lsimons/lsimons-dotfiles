#!/usr/bin/env python3
"""Installation script for Go"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists, brew_install


def main():
    info("Installing Go...")

    if command_exists('go'):
        success("Go already installed")
        return 0

    if brew_install('go'):
        success("Go installed")
        return 0

    error("Failed to install Go")
    return 1


if __name__ == '__main__':
    sys.exit(main())
