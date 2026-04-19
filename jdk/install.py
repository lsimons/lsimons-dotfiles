#!/usr/bin/env python3
"""Install OpenJDK via mise.

Note: jdk/path.sh still sets JAVA_HOME to IntelliJ's bundled JBR when
present. mise activation runs after path.sh and will override JAVA_HOME
with the mise-managed JDK for users who want a command-line default.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists


def main():
    info("Installing OpenJDK via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    try:
        subprocess.run(['mise', 'use', '-g', 'java@temurin-21'], check=True)
    except subprocess.CalledProcessError:
        error("Failed to install OpenJDK via mise")
        return 1

    success("OpenJDK installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
