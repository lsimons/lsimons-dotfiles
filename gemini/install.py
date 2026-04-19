#!/usr/bin/env python3
"""Installation script for Gemini CLI"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    brew_install,
    command_exists,
    error,
    info,
    is_dry_run,
    link_file,
    parse_dry_run,
    success,
)


def configure_gemini():
    home = Path.home()
    dotfiles = home / '.dotfiles'
    gemini_dir = home / '.gemini'
    gemini_md = gemini_dir / 'GEMINI.md'
    claude_md_source = dotfiles / 'claude' / 'CLAUDE.md.symlink'

    if not is_dry_run():
        gemini_dir.mkdir(parents=True, exist_ok=True)

    link_file(claude_md_source, gemini_md)


def main():
    parse_dry_run()
    info("Installing Gemini CLI...")

    if command_exists('gemini'):
        success("Gemini CLI already installed")
    elif brew_install('gemini-cli'):
        success("Gemini CLI installed")
    else:
        error("Failed to install Gemini CLI")
        return 1

    configure_gemini()
    return 0


if __name__ == '__main__':
    sys.exit(main())
