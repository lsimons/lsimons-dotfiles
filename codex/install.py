#!/usr/bin/env python3
"""Installation script for Codex CLI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    brew_install,
    brew_is_installed,
    error,
    info,
    is_dry_run,
    link_file,
    parse_dry_run,
    success,
)


def install_codex():
    """Install Codex via Homebrew."""
    info("Installing Codex...")

    if brew_is_installed("codex"):
        success("Codex already installed")
        return 0

    if brew_install("codex", cask=True):
        success("Codex installed")
        return 0

    error("Failed to install Codex")
    return 1


def configure_codex():
    """Configure Codex symlinks."""
    home = Path.home()
    dotfiles = home / ".dotfiles"
    codex_dir = home / ".codex"

    if not is_dry_run():
        codex_dir.mkdir(parents=True, exist_ok=True)

    link_file(dotfiles / "codex" / "config.toml.symlink", codex_dir / "config.toml")
    link_file(dotfiles / "codex" / "models.json.symlink", codex_dir / "models.json")


def main():
    parse_dry_run()
    info("Setting up Codex...")

    result = install_codex()
    if result != 0:
        return result

    configure_codex()
    return 0


if __name__ == "__main__":
    sys.exit(main())
