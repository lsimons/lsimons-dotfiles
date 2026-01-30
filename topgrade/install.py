#!/usr/bin/env python3
"""Installation script for topgrade (automated system updater)"""

import subprocess
import sys


def main():
    print("[INFO] Installing topgrade...")

    # Check if already installed
    result = subprocess.run(['which', 'topgrade'], capture_output=True)
    if result.returncode == 0:
        print("[SUCCESS] topgrade already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', 'topgrade'], check=True)
        print("[SUCCESS] topgrade installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install topgrade", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
