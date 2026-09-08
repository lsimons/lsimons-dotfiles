#!/usr/bin/env python3
"""Install Python.

Installs the distribution's Python (Homebrew's python@3 on macOS, pacman's
python on Arch) so other native packages that depend on it keep working.
Then installs Python via mise so mise shims take precedence in interactive
shells, giving the user the mise-managed version.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    command_exists,
    ensure_package,
    error,
    info,
    install_symlinks,
    is_dry_run,
    mise_use,
    parse_dry_run,
    success,
)


def install_system_python():
    return ensure_package('System Python', brew='python@3', pacman='python')


def install_mise_python():
    if not command_exists('mise') and not is_dry_run():
        error("mise not found; install the 'mise' topic first")
        return False

    info("Installing Python via mise...")
    if not mise_use('python@3.14'):
        error("Failed to install Python via mise")
        return False

    success("mise Python installed")
    return True


def main():
    parse_dry_run()
    install_symlinks(Path(__file__).resolve().parent)

    if not install_system_python():
        return 1
    if not install_mise_python():
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
