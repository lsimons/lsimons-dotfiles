#!/usr/bin/env python3
"""Installation script for Quarto."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import ensure_package, info, parse_dry_run


def main():
    parse_dry_run()
    info("Installing Quarto...")

    # macOS: a cask whose pkg installer requires sudo; brew will prompt
    # for the password interactively.
    # Linux: quarto-cli-bin repackages upstream's x86_64 tarball, so it is
    # optional — there is nothing to install on aarch64.
    if not ensure_package(
        "Quarto",
        brew="quarto",
        cask=True,
        aur="quarto-cli-bin",
        command="quarto",
        optional=True,
    ):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
