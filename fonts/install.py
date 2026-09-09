#!/usr/bin/env python3
"""Installation script for fonts"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import ensure_package, error, info, parse_dry_run

# (label, brew cask, pacman package, apt package, optional). Arch splits
# and renames these: Homebrew's font-lilex + font-lilex-nerd-font are one
# ttf-lilex-nerd package, and there is no aarch64 build of Iosevka in the
# repos, so it is left to fontconfig's fallbacks rather than failing the
# run. Debian/Ubuntu package neither Iosevka nor Lilex at all, which makes
# Lilex optional too.
FONTS = [
    ("Cascadia Code", "font-cascadia-code", "ttf-cascadia-code", "fonts-cascadia-code", False),
    ("Iosevka", "font-iosevka", "otf-iosevka", None, True),
    ("JetBrains Mono", "font-jetbrains-mono", "ttf-jetbrains-mono", "fonts-jetbrains-mono", False),
    ("Lilex", "font-lilex", "ttf-lilex-nerd", None, True),
    ("Lilex Nerd Font", "font-lilex-nerd-font", "ttf-lilex-nerd", None, True),
]


def main():
    parse_dry_run()
    info("Installing fonts...")

    for label, brew, pacman, apt, optional in FONTS:
        if not ensure_package(
            label, brew=brew, cask=True, pacman=pacman, apt=apt, optional=optional
        ):
            error(f"Failed to install {label}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
