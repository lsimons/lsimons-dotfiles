#!/usr/bin/env python3
"""Installation script for mise (polyglot tool version manager).

Also installs a LaunchAgent that extends launchd's PATH with mise's
shims directory, so GUI apps (Zed, VS Code, IntelliJ, etc.) launched
from Finder / Dock can find mise-managed tools.
"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    DOTFILES_ROOT, info, success, error, command_exists, brew_install,
)


def install_mise():
    if command_exists('mise'):
        success("mise already installed")
        return True

    if brew_install('mise'):
        success("mise installed")
        return True

    error("Failed to install mise")
    return False


def install_launch_agent():
    home = Path.home()
    xdg_data_home = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share'))
    shims_path = xdg_data_home / 'mise' / 'shims'

    plist_name = 'com.lsimons.mise-gui-path.plist'
    template = DOTFILES_ROOT / 'mise' / plist_name
    agents_dir = home / 'Library' / 'LaunchAgents'
    dest = agents_dir / plist_name

    content = template.read_text().replace('__MISE_SHIMS__', str(shims_path))

    agents_dir.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        subprocess.run(
            ['launchctl', 'unload', str(dest)],
            capture_output=True,
        )

    if dest.exists() and dest.read_text() == content:
        subprocess.run(
            ['launchctl', 'load', str(dest)],
            capture_output=True,
        )
        success("mise-gui-path LaunchAgent already up to date")
        return True

    dest.write_text(content)
    subprocess.run(['launchctl', 'load', str(dest)], capture_output=True)
    success(
        "Installed mise-gui-path LaunchAgent "
        "(GUI apps will see mise shims after next login)"
    )
    return True


def main():
    info("Installing mise...")

    if not install_mise():
        return 1

    install_launch_agent()
    return 0


if __name__ == '__main__':
    sys.exit(main())
