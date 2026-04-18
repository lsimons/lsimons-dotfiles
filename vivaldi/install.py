#!/usr/bin/env python3
"""Installation script for Vivaldi Browser"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, app_exists, brew_install


def main():
    info("Installing Vivaldi Browser...")

    if app_exists('Vivaldi'):
        success("Vivaldi Browser already installed")
        return 0

    if brew_install('vivaldi', cask=True):
        success("Vivaldi Browser installed")
        return 0

    error("Failed to install Vivaldi Browser")
    return 1


if __name__ == '__main__':
    sys.exit(main())
