#!/usr/bin/env python3
"""Installation script for OpenCode"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    brew_install,
    brew_is_installed,
    dry,
    error,
    info,
    SKILLS_DIR,
    is_dry_run,
    link_directory,
    link_file,
    parse_dry_run,
    render_agents_md,
    success,
)


def install_opencode():
    """Install OpenCode via the anomalyco Homebrew tap."""
    formula = "anomalyco/tap/opencode"
    info("Installing OpenCode...")

    if brew_is_installed(formula):
        success("OpenCode already installed")
        return 0

    if brew_install(formula):
        success("OpenCode installed")
        return 0

    error("Failed to install OpenCode")
    return 1


def configure_opencode():
    """Configure OpenCode symlinks."""
    home = Path.home()
    xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    dotfiles = home / ".dotfiles"
    opencode_dir = xdg_config_home / "opencode"
    agents_md = opencode_dir / "AGENTS.md"
    config_json = opencode_dir / "opencode.json"
    config_json_source = dotfiles / "opencode" / "opencode.json.symlink"
    legacy_config_json = opencode_dir / "config.json"
    tui_json = opencode_dir / "tui.json"
    tui_json_source = dotfiles / "opencode" / "tui.json.symlink"
    themes_source = dotfiles / "opencode" / "themes"

    if not is_dry_run():
        opencode_dir.mkdir(parents=True, exist_ok=True)

    render_agents_md(agents_md)
    link_file(config_json_source, config_json)
    link_file(tui_json_source, tui_json)
    link_directory(themes_source, opencode_dir / "themes")
    link_directory(SKILLS_DIR, opencode_dir / "skills")

    if legacy_config_json.is_symlink():
        if is_dry_run():
            dry(f"would remove legacy symlink {legacy_config_json}")
        else:
            legacy_config_json.unlink()


def main():
    parse_dry_run()
    info("Setting up OpenCode...")

    result = install_opencode()
    if result != 0:
        return result

    configure_opencode()
    return 0


if __name__ == "__main__":
    sys.exit(main())
