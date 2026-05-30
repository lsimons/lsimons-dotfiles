#!/usr/bin/env python3
"""Installation script for the macOS Dock.

Pins a fixed set of apps to the Dock using dockutil. This topic runs last
in the install sequence (see script/install.py's FINAL_TOPICS) so the apps
it references have already been installed by their own topics.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    brew_install,
    command_exists,
    error,
    info,
    is_dry_run,
    parse_dry_run,
    run_cmd,
    success,
    warn,
)

# Apps to pin, in Dock order. Absolute paths to .app bundles.
DOCK_APPS = [
    "/Applications/Vivaldi.app",
    "/Applications/Ghostty.app",
    "/Applications/Zed.app",
    "/Applications/1Password.app",
    "/System/Applications/System Settings.app",
]


def ensure_dockutil():
    if command_exists("dockutil"):
        success("dockutil already installed")
        return True
    return brew_install("dockutil")


def current_dock_labels():
    """Return the set of app labels currently pinned in the Dock."""
    result = run_cmd(["dockutil", "--list"], capture_output=True)
    labels = set()
    for line in (result.stdout or "").splitlines():
        if line.strip():
            labels.add(line.split("\t", 1)[0])
    return labels


def main():
    parse_dry_run()
    info("Configuring macOS Dock...")

    if not ensure_dockutil():
        error("Failed to install dockutil")
        return 1

    existing = set() if is_dry_run() else current_dock_labels()

    added = False
    for app_path in DOCK_APPS:
        path = Path(app_path)
        label = path.stem
        if not is_dry_run() and not path.exists():
            warn(f"Skipping {label}: {app_path} not found")
            continue
        if label in existing:
            success(f"{label} already in Dock")
            continue
        run_cmd(["dockutil", "--add", app_path, "--no-restart"])
        success(f"Added {label} to Dock")
        added = True

    if added:
        run_cmd(["killall", "Dock"])
        success("Dock restarted")
    else:
        success("Dock already up to date")

    return 0


if __name__ == "__main__":
    sys.exit(main())
