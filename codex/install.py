#!/usr/bin/env python3
"""Installation script for Codex CLI."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    brew_install,
    brew_is_installed,
    error,
    info,
    SKILLS_DIR,
    is_dry_run,
    link_directory,
    link_file,
    parse_dry_run,
    render_agents_md,
    success,
    write_file,
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


def write_config(codex_dir, topic_dir):
    """Write ~/.codex/config.toml with the AI-specific git config."""
    config_path = codex_dir / "config.toml"
    config = (topic_dir / "config.toml.base").read_text()
    xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    git_config = xdg_config_home / "git" / "config.ai"
    config += (
        "\n[shell_environment_policy]\n"
        f"set = {{ GIT_CONFIG_GLOBAL = {json.dumps(str(git_config))} }}\n"
    )

    if config_path.is_symlink() and not is_dry_run():
        config_path.unlink()

    write_file(config_path, config)
    success(f"Wrote: {config_path}")


def configure_codex():
    """Configure Codex."""
    home = Path.home()
    dotfiles = home / ".dotfiles"
    codex_dir = home / ".codex"
    agents_md = codex_dir / "AGENTS.md"
    topic_dir = Path(__file__).resolve().parent

    if not is_dry_run():
        codex_dir.mkdir(parents=True, exist_ok=True)

    render_agents_md(agents_md)
    write_config(codex_dir, topic_dir)
    link_file(dotfiles / "codex" / "models.json.symlink", codex_dir / "models.json")
    link_directory(dotfiles / "codex" / "rules", codex_dir / "rules")
    link_directory(SKILLS_DIR, codex_dir / "skills")


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
