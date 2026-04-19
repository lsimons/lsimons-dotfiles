#!/usr/bin/env python3
"""Install Python via mise.

Note: the bootstrap Python (the one running install.py itself) comes from
Homebrew — see script/install.py. This topic installs the Python that the
user's interactive shells will see on PATH via mise shims.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists


def main():
    info("Installing Python via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    try:
        subprocess.run(['mise', 'use', '-g', 'python@3.14'], check=True)
    except subprocess.CalledProcessError:
        error("Failed to install Python via mise")
        return 1

    success("Python installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
