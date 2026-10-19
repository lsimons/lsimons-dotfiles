#!/usr/bin/env python3
"""Installation script for Zed editor"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    XDG_CONFIG_HOME,
    ensure_package,
    info,
    install_symlinks,
    link_or_merge_json,
    parse_dry_run,
    private_overlay,
)


def main():
    parse_dry_run()
    topic_dir = Path(__file__).resolve().parent
    install_symlinks(topic_dir)
    # Not in symlinks.txt: the private overlay adds the LiteLLM provider,
    # and then settings.json is a merged file instead of a symlink.
    link_or_merge_json(
        topic_dir / 'settings.json.base',
        XDG_CONFIG_HOME / 'zed' / 'settings.json',
        private_overlay('zed', 'settings.json'),
    )

    info("Installing Zed...")

    # The Linux binary is called `zeditor`, not `zed` — `zed` is taken by
    # an unrelated Z-shell utility on some distributions. Optional there
    # because Arch only ships zed for x86_64; the config symlinks above
    # are installed regardless so the editor is configured if it exists.
    if not ensure_package(
        'Zed',
        brew='zed',
        cask=True,
        macos_app='Zed',
        pacman='zed',
        command='zeditor',
        optional=True,
    ):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
