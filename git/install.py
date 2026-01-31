#!/usr/bin/env python3
"""Installation script for Git"""

import subprocess
import sys


def main():
    print("[INFO] Installing Git...")

    # Check if already installed via Homebrew
    result = subprocess.run(['brew', 'list', 'git'], capture_output=True)
    if result.returncode == 0:
        print("[SUCCESS] Git already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', 'git'], check=True)
        print("[SUCCESS] Git installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install Git", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
