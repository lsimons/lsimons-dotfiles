#!/usr/bin/env python3
"""Installation script for tfenv and Terraform"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    brew_install,
    brew_is_installed,
    error,
    info,
    parse_dry_run,
    run_cmd,
    success,
)


def main():
    parse_dry_run()
    info("Installing tfenv and Terraform...")

    if brew_is_installed('tfenv'):
        success("tfenv already installed")
    else:
        info("Installing tfenv via Homebrew...")
        if not brew_install('tfenv'):
            error("Failed to install tfenv")
            return 1
        success("tfenv installed")

    info("Installing latest stable Terraform...")
    try:
        run_cmd(['tfenv', 'install', 'latest'], check=True)
        run_cmd(['tfenv', 'use', 'latest'], check=True)
        success("Terraform installed")
    except subprocess.CalledProcessError:
        error("Failed to install Terraform via tfenv")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
