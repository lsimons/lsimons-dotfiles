#!/usr/bin/env python3
"""Installation script for GitHub CLI"""

import subprocess
import sys


def main():
    print("[INFO] Installing GitHub CLI...")

    # Check if already installed
    result = subprocess.run(['which', 'gh'], capture_output=True)
    if result.returncode == 0:
        print("[SUCCESS] GitHub CLI already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', 'gh'], check=True)
        print("[SUCCESS] GitHub CLI installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install GitHub CLI", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
