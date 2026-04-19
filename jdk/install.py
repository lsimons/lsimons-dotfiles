#!/usr/bin/env python3
"""Install OpenJDK via mise.

Note: jdk/path.sh still sets JAVA_HOME to IntelliJ's bundled JBR when
present. mise activation runs after path.sh and will override JAVA_HOME
with the mise-managed JDK for users who want a command-line default.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import command_exists, error, info, mise_use, parse_dry_run, success


def main():
    parse_dry_run()
    info("Installing OpenJDK via mise...")

    if not command_exists('mise'):
        error("mise not found; install the 'mise' topic first")
        return 1

    if not mise_use('java@temurin-21'):
        error("Failed to install OpenJDK via mise")
        return 1

    success("OpenJDK installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
