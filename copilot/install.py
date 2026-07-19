#!/usr/bin/env python3
"""Installation script for GitHub Copilot CLI"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    brew_install,
    brew_is_installed,
    error,
    SKILLS_DIR,
    info,
    is_dry_run,
    link_directory,
    parse_dry_run,
    render_agents_md,
    success,
)


def install_copilot_cli():
    """Install copilot-cli via Homebrew"""
    info("Installing copilot-cli...")

    if brew_is_installed("copilot-cli"):
        success("copilot-cli already installed")
        return 0

    if brew_install("copilot-cli"):
        success("copilot-cli installed")
        return 0

    error("Failed to install copilot-cli")
    return 1


def configure_copilot():
    """Configure copilot-instructions.md symlink"""
    home = Path.home()
    copilot_dir = home / ".copilot"
    instructions_md = copilot_dir / "copilot-instructions.md"

    # Ensure ~/.copilot exists
    if not is_dry_run():
        copilot_dir.mkdir(parents=True, exist_ok=True)

    render_agents_md(instructions_md)
    link_directory(SKILLS_DIR, copilot_dir / "skills")


def main():
    parse_dry_run()
    info("Setting up GitHub Copilot CLI...")

    result = install_copilot_cli()
    if result != 0:
        return result

    configure_copilot()
    return 0


if __name__ == "__main__":
    sys.exit(main())
