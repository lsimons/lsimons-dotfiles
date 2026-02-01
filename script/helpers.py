"""Common helper functions for topic install scripts."""

import json
import socket
import subprocess
import sys
from pathlib import Path

# Root of the dotfiles repository
DOTFILES_ROOT = Path(__file__).resolve().parent.parent


def info(msg):
    """Print an info message."""
    print(f"[INFO] {msg}")


def success(msg):
    """Print a success message."""
    print(f"[SUCCESS] {msg}")


def error(msg):
    """Print an error message to stderr."""
    print(f"[ERROR] {msg}", file=sys.stderr)


def command_exists(cmd):
    """Check if a command exists in PATH."""
    result = subprocess.run(['which', cmd], capture_output=True)
    return result.returncode == 0


def app_exists(app_name):
    """Check if a macOS app exists in /Applications.

    Args:
        app_name: Name without .app suffix (e.g., 'Brave Browser')
    """
    return Path(f'/Applications/{app_name}.app').exists()


def brew_install(package, cask=False):
    """Install a package via Homebrew.

    Args:
        package: The brew formula or cask name
        cask: If True, install as cask (--cask flag)

    Returns:
        True on success, False on failure
    """
    cmd = ['brew', 'install']
    if cask:
        cmd.append('--cask')
    cmd.append(package)

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def brew_is_installed(package):
    """Check if a package is installed via Homebrew."""
    result = subprocess.run(['brew', 'list', package], capture_output=True)
    return result.returncode == 0


def get_short_hostname():
    """Get short hostname (without domain suffix)."""
    return socket.gethostname().split('.')[0]


def get_machine_config():
    """Load machine-specific configuration.

    Looks for machines/<hostname>.json, falls back to machines/default.json.

    Returns:
        tuple: (config_dict, hostname)
    """
    hostname = get_short_hostname()
    machines_dir = DOTFILES_ROOT / 'machines'

    # Try machine-specific config first
    config_file = machines_dir / f'{hostname}.json'
    if not config_file.exists():
        config_file = machines_dir / 'default.json'

    with open(config_file) as f:
        return json.load(f), hostname
