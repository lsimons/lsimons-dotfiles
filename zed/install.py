#!/usr/bin/env python3
"""Installation script for Zed editor"""

import subprocess
import sys
from pathlib import Path


def main():
    print("[INFO] Installing Zed...")

    # Check if already installed
    app_path = Path('/Applications/Zed.app')
    if app_path.exists():
        print("[SUCCESS] Zed already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', '--cask', 'zed'], check=True)
        print("[SUCCESS] Zed installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install Zed", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
