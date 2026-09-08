#!/usr/bin/env python3
"""Installation script for ZSH configuration"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    IS_LINUX,
    command_exists,
    ensure_package,
    info,
    install_symlinks,
    parse_dry_run,
)


def main():
    parse_dry_run()
    install_symlinks(Path(__file__).resolve().parent)

    # macOS has shipped zsh as the default login shell since Catalina, so
    # this is a no-op there. Arch installs bash only.
    zsh_was_present = command_exists("zsh")
    if not ensure_package("zsh", brew="zsh", pacman="zsh", command="zsh"):
        return 1

    # Deliberately not running chsh: on Omarchy the login shell is bash
    # and the desktop's own integrations are written for it, so switching
    # it is the user's call, not the installer's.
    if IS_LINUX and not zsh_was_present:
        info("zsh installed. To make it your login shell, run:")
        info("  chsh -s /usr/bin/zsh")

    return 0


if __name__ == "__main__":
    sys.exit(main())
