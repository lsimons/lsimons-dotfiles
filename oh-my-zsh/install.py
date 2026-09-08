#!/usr/bin/env python3
"""Installation script for Oh My Zsh"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    ensure_package,
    error,
    info,
    install_symlinks,
    is_dry_run,
    parse_dry_run,
    run_cmd,
    success,
)


def install_oh_my_zsh():
    info("Installing Oh My Zsh...")

    oh_my_zsh_dir = Path.home() / '.oh-my-zsh'
    if not is_dry_run() and oh_my_zsh_dir.exists():
        success("Oh My Zsh already installed")
        return True

    try:
        env = os.environ.copy()
        env['RUNZSH'] = 'no'
        env['CHSH'] = 'no'

        omz_url = (
            "https://raw.githubusercontent.com"
            "/ohmyzsh/ohmyzsh/master/tools/install.sh"
        )
        run_cmd(
            ['sh', '-c', f'curl -fsSL {omz_url} | sh'],
            check=True,
            env=env,
        )
        success("Oh My Zsh installed")
        return True
    except subprocess.CalledProcessError:
        error("Failed to install Oh My Zsh")
        return False


def install_powerlevel10k():
    info("Installing powerlevel10k...")

    # Arch names the package after what it is rather than after the
    # theme; oh-my-zsh/powerline10k.zsh knows both install prefixes.
    return ensure_package(
        'powerlevel10k',
        brew='powerlevel10k',
        aur='zsh-theme-powerlevel10k',
    )


def main():
    parse_dry_run()

    install_symlinks(Path(__file__).resolve().parent)
    if not install_oh_my_zsh():
        return 1
    if not install_powerlevel10k():
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
