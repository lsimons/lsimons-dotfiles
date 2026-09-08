#!/usr/bin/env python3
"""Installation script for a container runtime.

macOS gets Rancher Desktop, which bundles the VM, the docker CLI and a
Kubernetes distribution in one app. Linux runs containers natively, so
there is no VM to install: it gets the docker engine plus the compose and
buildx plugins, the socket enabled, and the invoking user added to the
`docker` group.
"""

import getpass
import grp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    IS_LINUX,
    dry,
    ensure_package,
    error,
    info,
    is_dry_run,
    parse_dry_run,
    run_cmd,
    success,
    warn,
)

LINUX_PACKAGES = [
    ("docker", "docker"),
    ("docker-compose", "docker-compose"),
    ("docker-buildx", "docker-buildx"),
]


def install_linux_docker():
    for label, package in LINUX_PACKAGES:
        if not ensure_package(label, pacman=package):
            return False
    return enable_docker_service() and join_docker_group()


def enable_docker_service():
    """Enable and start docker.socket so the daemon starts on demand."""
    if is_dry_run():
        dry("would run: sudo systemctl enable --now docker.socket")
        return True

    result = run_cmd(
        ['sudo', 'systemctl', 'enable', '--now', 'docker.socket'],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        error(f"Failed to enable docker.socket: {(result.stderr or '').strip()}")
        return False
    success("docker.socket enabled")
    return True


def join_docker_group():
    """Add the current user to the `docker` group.

    Membership of this group is root-equivalent — it grants the ability to
    start a container that bind-mounts the host filesystem. That is the
    standard single-user desktop trade-off (and what Omarchy's own
    installer does), taken deliberately here so `docker` works without
    sudo. Drop this call and use rootless docker instead if that trade is
    not wanted on a given machine.
    """
    user = getpass.getuser()

    if is_dry_run():
        dry(f"would add {user} to the docker group")
        return True

    try:
        if user in grp.getgrnam('docker').gr_mem:
            success(f"{user} is already in the docker group")
            return True
    except KeyError:
        warn("No docker group exists; skipping group membership")
        return True

    result = run_cmd(
        ['sudo', 'usermod', '-aG', 'docker', user], check=False, capture_output=True
    )
    if result.returncode != 0:
        error(f"Failed to add {user} to the docker group: {(result.stderr or '').strip()}")
        return False
    success(f"Added {user} to the docker group (log out and back in to pick it up)")
    return True


def main():
    parse_dry_run()

    if IS_LINUX:
        info("Installing the docker engine...")
        return 0 if install_linux_docker() else 1

    info("Checking Rancher Desktop installation...")
    if not ensure_package(
        'Rancher Desktop', brew='rancher', cask=True, macos_app='Rancher Desktop'
    ):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
