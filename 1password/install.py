#!/usr/bin/env python3
"""Installation script for 1Password CLI"""

import subprocess
import sys


def main():
    print("[INFO] Installing 1Password CLI...")

    # Check if already installed
    result = subprocess.run(['which', 'op'], capture_output=True)
    if result.returncode == 0:
        print("[SUCCESS] 1Password CLI already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', '--cask', '1password-cli'], check=True)
        print("[SUCCESS] 1Password CLI installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install 1Password CLI", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
