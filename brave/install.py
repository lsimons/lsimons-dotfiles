#!/usr/bin/env python3
"""Installation script for Brave Browser"""

import subprocess
import sys
from pathlib import Path


def main():
    print("[INFO] Installing Brave Browser...")

    # Check if already installed
    app_path = Path('/Applications/Brave Browser.app')
    if app_path.exists():
        print("[SUCCESS] Brave Browser already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', '--cask', 'brave-browser'], check=True)
        print("[SUCCESS] Brave Browser installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install Brave Browser", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
