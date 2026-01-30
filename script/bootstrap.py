#!/usr/bin/env python3
"""
Bootstrap script for lsimons-dotfiles
This script is safe to run multiple times (idempotent)
It symlinks files ending in .symlink to the appropriate locations

Inspired by https://github.com/holman/dotfiles
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def info(message):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def warn(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")


def error(message):
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def backup_file(file_path):
    """Backup a file before replacing it"""
    path = Path(file_path)
    if path.exists() or path.is_symlink():
        backup_dir = Path.home() / '.dotfiles-backup' / datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir.mkdir(parents=True, exist_ok=True)
        dest = backup_dir / path.name
        shutil.move(str(path), str(dest))
        info(f"Backed up {file_path} to {dest}")


def link_file(src, dst):
    """Link a file to its destination"""
    src_path = Path(src)
    dst_path = Path(dst)

    # Check if destination already exists and is correct
    if dst_path.is_symlink():
        current_src = dst_path.resolve()
        if current_src == src_path.resolve():
            success(f"Already linked: {dst}")
            return True
        else:
            warn(f"Symlink exists but points to different location: {dst} -> {current_src}")
            backup_file(dst)
    elif dst_path.exists():
        warn(f"File exists: {dst}")
        backup_file(dst)

    # Create parent directory if it doesn't exist
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Create symlink
    dst_path.symlink_to(src_path)
    success(f"Linked: {dst} -> {src}")
    return True


def setup_xdg():
    """Setup XDG Base Directory structure"""
    info("Setting up XDG Base Directory structure...")

    home = Path.home()
    xdg_config_home = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
    xdg_data_home = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share'))
    xdg_cache_home = Path(os.environ.get('XDG_CACHE_HOME', home / '.cache'))
    xdg_state_home = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state'))

    xdg_config_home.mkdir(parents=True, exist_ok=True)
    xdg_data_home.mkdir(parents=True, exist_ok=True)
    xdg_cache_home.mkdir(parents=True, exist_ok=True)
    xdg_state_home.mkdir(parents=True, exist_ok=True)

    success("XDG directories created")


def main():
    """Main bootstrap flow"""
    info("Starting dotfiles bootstrap...")

    # Get dotfiles root directory
    script_dir = Path(__file__).parent
    dotfiles_root = script_dir.parent
    info(f"Dotfiles root: {dotfiles_root}")

    # Setup XDG directories first
    setup_xdg()

    # Find all .symlink files and link them
    info("Linking dotfiles...")

    home = Path.home()
    xdg_config_home = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))

    for src in dotfiles_root.rglob('*.symlink'):
        if src.is_file():
            # Determine destination
            basename = src.stem  # filename without .symlink extension

            # Special handling for specific files
            if basename == 'zshrc':
                dst = home / '.zshrc'
            elif basename == 'gitconfig':
                dst = xdg_config_home / 'git' / 'config'
            elif basename == 'pythonrc':
                dst = xdg_config_home / 'python' / 'pythonrc'
            else:
                # Default: link to home directory with a dot prefix
                dst = home / f'.{basename}'

            link_file(src, dst)

    success("Bootstrap complete!")
    info("")
    info("Next steps:")
    info("  1. Run 'source ~/.zshrc' to load the new configuration")
    info("  2. (Optional) Run 'script/install.py' to run topic-specific installations")
    info("  3. Configure 1Password CLI for secret management")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        warn("Bootstrap cancelled by user")
        sys.exit(130)
    except Exception as e:
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
