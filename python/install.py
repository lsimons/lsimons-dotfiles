#!/usr/bin/env python3
"""Installation script for Python configuration"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists, brew_install


def main():
    info("Installing Python...")

    if command_exists('python3'):
        success("python3 already installed")
    elif brew_install('python3'):
        success("python3 installed")
    else:
        error("Failed to install python3")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
