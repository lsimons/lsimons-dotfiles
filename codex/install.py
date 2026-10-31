#!/usr/bin/env python3
"""Installation script for Codex CLI."""

import json
import os
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    SKILLS_DIR,
    ensure_package,
    error,
    info,
    is_dry_run,
    link_directory,
    link_file,
    parse_dry_run,
    private_overlay,
    render_agents_md,
    success,
    write_file,
)


def split_toml_overlay(text):
    """Split a TOML overlay into (top-level keys, tables).

    Top-level keys must come before the first table header, so the
    overlay's keys go in front of the base config and its tables after it.
    """
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.lstrip().startswith("["):
            return "".join(lines[:index]), "".join(lines[index:])
    return text, ""


def install_codex():
    """Install the Codex CLI."""
    info("Installing Codex...")

    # Omarchy's pacman repo carries openai-codex-bin, prebuilt for aarch64.
    if not ensure_package(
        "Codex",
        brew="codex",
        cask=True,
        pacman="openai-codex-bin",
        mise="codex",
        command="codex",
    ):
        return 1
    return 0


def write_config(codex_dir, topic_dir):
    """Write ~/.codex/config.toml with the AI-specific git config.

    A private overlay (codex/config.toml in the private repository) adds
    work-only settings such as the model provider; it may not repeat a key
    the base config sets.
    """
    config_path = codex_dir / "config.toml"
    config = (topic_dir / "config.toml.base").read_text()
    overlay = private_overlay("codex", "config.toml")
    if overlay is not None:
        overlay_keys, overlay_tables = split_toml_overlay(overlay.read_text())
        config = f"{overlay_keys}\n{config}\n{overlay_tables}"
        info(f"Merging private overlay: {overlay}")
    xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    git_config = xdg_config_home / "git" / "config.ai"
    config += (
        "\n[shell_environment_policy]\n"
        f"set = {{ GIT_CONFIG_GLOBAL = {json.dumps(str(git_config))} }}\n"
    )

    try:
        tomllib.loads(config)
    except tomllib.TOMLDecodeError as exc:
        error(f"Codex config is not valid TOML after merging overlays: {exc}")
        return False

    if config_path.is_symlink() and not is_dry_run():
        config_path.unlink()

    write_file(config_path, config)
    success(f"Wrote: {config_path}")
    return True


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
    if not write_config(codex_dir, topic_dir):
        return False
    link_file(dotfiles / "codex" / "models.json.symlink", codex_dir / "models.json")
    link_directory(dotfiles / "codex" / "rules", codex_dir / "rules")
    link_directory(SKILLS_DIR, codex_dir / "skills")
    return True


def main():
    parse_dry_run()
    info("Setting up Codex...")

    result = install_codex()
    if result != 0:
        return result

    if not configure_codex():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
