#!/usr/bin/env python3
"""Installation script for Ghostty terminal"""

import subprocess
import sys
from pathlib import Path


def main():
    print("[INFO] Installing Ghostty...")

    # Check if already installed
    app_path = Path('/Applications/Ghostty.app')
    if app_path.exists():
        print("[SUCCESS] Ghostty already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', '--cask', 'ghostty'], check=True)
        print("[SUCCESS] Ghostty installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install Ghostty", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
