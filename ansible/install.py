#!/usr/bin/env python3
"""Installation script for Ansible and related tools"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import ensure_package, error, info, parse_dry_run, success

# (label, brew formula, pacman package, apt package) — the names happen to
# match on every platform, but keep them explicit so a divergence is a
# data change.
PACKAGES = [
    ("ansible", "ansible", "ansible", "ansible"),
    ("ansible-lint", "ansible-lint", "ansible-lint", "ansible-lint"),
    ("yamllint", "yamllint", "yamllint", "yamllint"),
]


def main():
    parse_dry_run()
    info("Installing Ansible and related tools...")

    failed = [
        label
        for label, brew, pacman, apt in PACKAGES
        if not ensure_package(label, brew=brew, pacman=pacman, apt=apt)
    ]

    if failed:
        error(f"Failed to install: {', '.join(failed)}")
        return 1

    success("Ansible and related tools installed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
