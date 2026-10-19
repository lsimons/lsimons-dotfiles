#!/usr/bin/env python3
"""Installation script for fnox (1Password secret injection via mise)

Installed via `mise use -g github:jdx/fnox`: a prebuilt release binary,
no Rust toolchain / cargo compile needed.

The backend is spelled out rather than using the bare registry name
`fnox`. Since mise 2026.9 the registry resolves `fnox` to the packslip
backend first, and packslip only ever offers the latest release. With
`settings.minimum_release_age` (see the `mise` topic) that single
candidate is rejected whenever upstream shipped within the last week,
and mise reports "no versions found matching date filter" instead of
falling back to the `github:` backend. The github backend lists every
release, so the age gate simply picks the newest one that is old
enough.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    command_exists,
    error,
    info,
    is_dry_run,
    mise_use,
    parse_dry_run,
    success,
)

MISE_TOOL = 'github:jdx/fnox'


def main():
    parse_dry_run()
    info("Installing fnox...")

    if not command_exists('mise') and not is_dry_run():
        error("mise not found; install the 'mise' topic first")
        return 1

    if command_exists('fnox'):
        success("fnox already installed")
        return 0

    if not mise_use(MISE_TOOL):
        error(f"Failed to install fnox via 'mise use -g {MISE_TOOL}'")
        return 1

    success("fnox installed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
