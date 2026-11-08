#!/usr/bin/env python3
"""Reinstall the dotfiles' global npm CLIs into the active node.

`npm install -g` puts a package under one node version. When mise moves
node to a newer release (node is pinned to "24", so every patch release
counts), the new version starts with no global packages, and topgrade's
mise step then prunes the old version along with everything installed in
it. What is left is a mise shim that fails with "<tool> is not provided by
the active node".

mise has no default-packages file for node (it does for go, python and
ruby), so topgrade runs this script after every upgrade instead. It only
installs what is missing from the active node; topgrade's npm step keeps
the installed packages up to date.

The topic installers stay the owners of these packages: they install them
on a fresh machine and handle migrations such as renamed packages. This
list only repeats the package names, and a unit test checks that each one
still appears in its owning topic's installer. agent-browser is not listed
because topgrade's "agent skills" command already repairs it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    error,
    info,
    npm_global_installed,
    npm_install_global,
    parse_dry_run,
    success,
)

# (npm package, topic whose install.py owns it)
NPM_GLOBALS = (
    ("@earendil-works/pi-coding-agent", "pi-coding-agent"),
    ("@google/gemini-cli", "gemini"),
    ("@fission-ai/openspec", "openspec"),
    ("ccusage", "claude"),
)


def main():
    parse_dry_run()
    failed = []
    for package, topic in NPM_GLOBALS:
        if npm_global_installed(package):
            success(f"{package} already installed")
            continue
        info(f"Reinstalling {package} (from the {topic} topic) into the active node...")
        if npm_install_global(package):
            success(f"{package} installed")
        else:
            error(f"Failed to install {package}")
            failed.append(package)

    if failed:
        error(f"Could not reinstall: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
