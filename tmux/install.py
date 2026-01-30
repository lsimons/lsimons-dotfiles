#!/usr/bin/env python3
"""Installation script for tmux"""

import subprocess
import sys


def main():
    print("[INFO] Installing tmux...")

    # Check if already installed
    result = subprocess.run(['which', 'tmux'], capture_output=True)
    if result.returncode == 0:
        print("[SUCCESS] tmux already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', 'tmux'], check=True)
        print("[SUCCESS] tmux installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install tmux", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
