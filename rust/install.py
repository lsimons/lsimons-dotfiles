#!/usr/bin/env python3
"""Installation script for Rust via rustup"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error, command_exists


def main():
    xdg_data_home = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))
    rustup_home = Path(xdg_data_home) / 'rustup'
    cargo_home = Path(xdg_data_home) / 'cargo'
    cargo_bin = cargo_home / 'bin'

    env = os.environ.copy()
    env['RUSTUP_HOME'] = str(rustup_home)
    env['CARGO_HOME'] = str(cargo_home)

    info("Installing Rust via rustup...")

    rustup_bin = cargo_bin / 'rustup'
    if rustup_bin.exists():
        success("rustup already installed")
    else:
        info("Downloading and running rustup-init...")
        try:
            subprocess.run(
                ['sh', '-c', 'curl --proto =https --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path'],
                check=True,
                env=env
            )
            success("rustup installed")
        except subprocess.CalledProcessError:
            error("Failed to install rustup")
            return 1

    info("Installing latest stable Rust toolchain...")
    try:
        subprocess.run(
            [str(rustup_bin), 'toolchain', 'install', 'stable', '--no-self-update'],
            check=True,
            env=env
        )
        subprocess.run(
            [str(rustup_bin), 'default', 'stable'],
            check=True,
            env=env
        )
        success("Rust stable toolchain installed")
    except subprocess.CalledProcessError:
        error("Failed to install Rust stable toolchain")
        return 1

    info("Installing cargo-update...")
    cargo_bin_exe = cargo_bin / 'cargo'
    try:
        result = subprocess.run(
            [str(cargo_bin_exe), 'install', '--list'],
            capture_output=True,
            text=True,
            env=env
        )
        if 'cargo-update' in result.stdout:
            success("cargo-update already installed")
        else:
            subprocess.run(
                [str(cargo_bin_exe), 'install', 'cargo-update'],
                check=True,
                env=env
            )
            success("cargo-update installed")
    except subprocess.CalledProcessError:
        error("Failed to install cargo-update")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
