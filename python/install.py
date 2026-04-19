#!/usr/bin/env python3
"""Install Python.

Installs python@3 via Homebrew so other Homebrew packages that depend on it
continue to work. Then installs Python via mise so mise shims take precedence
in interactive shells, giving the user the mise-managed version.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    brew_install,
    brew_is_installed,
    command_exists,
    error,
    info,
    install_symlinks,
    mise_use,
    parse_dry_run,
    success,
)


def install_homebrew_python():
    if brew_is_installed('python@3'):
        info("Homebrew python@3 already installed")
        return True

    info("Installing python@3 via Homebrew...")
    if not brew_install('python@3'):
        error("Failed to install python@3 via Homebrew")
        return False

    success("Homebrew python@3 installed")
    return True


def install_mise_python():
    if not command_exists('mise'):
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

    if not install_homebrew_python():
        return 1
    if not install_mise_python():
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
