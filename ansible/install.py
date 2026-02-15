#!/usr/bin/env python3
"""Installation script for Ansible and related tools"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import brew_install, brew_is_installed, error, info, success

PACKAGES = ["ansible", "ansible-lint", "yamllint"]


def main():
    info("Installing Ansible and related tools...")

    failed = []
    for package in PACKAGES:
        if brew_is_installed(package):
            success(f"{package} already installed")
        else:
            info(f"Installing {package} via Homebrew...")
            if brew_install(package):
                success(f"{package} installed")
            else:
                error(f"Failed to install {package}")
                failed.append(package)

    if failed:
        error(f"Failed to install: {', '.join(failed)}")
        return 1

    success("Ansible and related tools installed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
