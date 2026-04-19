#!/usr/bin/env python3
"""Installation script for ZSH configuration"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, install_symlinks, make_dir, parse_dry_run, success


def main():
    parse_dry_run()
    install_symlinks(Path(__file__).resolve().parent)

    info("Setting up ZSH directories...")

    xdg_cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
    xdg_state = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state'))

    make_dir(xdg_cache / 'zsh')
    make_dir(xdg_state / 'zsh')

    success("ZSH directories configured")
    return 0


if __name__ == '__main__':
    sys.exit(main())
