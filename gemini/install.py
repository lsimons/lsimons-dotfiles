#!/usr/bin/env python3
"""Installation script for Gemini CLI"""

import subprocess
import sys


def main():
    print("[INFO] Installing Gemini CLI...")

    # Check if already installed
    result = subprocess.run(['which', 'gemini'], capture_output=True)
    if result.returncode == 0:
        print("[SUCCESS] Gemini CLI already installed")
        return 0

    # Install via Homebrew
    try:
        subprocess.run(['brew', 'install', 'gemini-cli'], check=True)
        print("[SUCCESS] Gemini CLI installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install Gemini CLI", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
