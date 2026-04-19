#!/usr/bin/env python3
"""Installation script for Rancher Desktop (docker)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import app_exists, brew_install, error, info, parse_dry_run, success


def main():
    parse_dry_run()
    info("Checking Rancher Desktop installation...")

    if app_exists('Rancher Desktop'):
        success("Rancher Desktop is already installed")
        return 0

    info("Installing Rancher Desktop via Homebrew...")
    if brew_install('rancher', cask=True):
        success("Rancher Desktop installed successfully")
        return 0
    else:
        error("Failed to install Rancher Desktop")
        return 1


if __name__ == '__main__':
    sys.exit(main())
