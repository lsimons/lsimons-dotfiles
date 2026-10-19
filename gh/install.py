#!/usr/bin/env python3
"""Installation script for GitHub CLI"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    ensure_package,
    info,
    is_dry_run,
    parse_dry_run,
    run_cmd,
    success,
    warn,
)

# gh extensions to install, as `owner/repo`. `github/gh-stack` provides the
# `gh stack` command for stacked pull requests.
EXTENSIONS = ['github/gh-stack']


def installed_extensions():
    """Return the set of installed extension repos, as lowercased `owner/repo`."""
    if is_dry_run():
        return set()
    try:
        result = run_cmd(['gh', 'extension', 'list'], capture_output=True)
    except subprocess.CalledProcessError:
        # No extensions installed at all makes older gh versions exit non-zero.
        return set()
    repos = set()
    for line in result.stdout.splitlines():
        # Columns are tab-separated: name, repo, version (plus optional flags).
        fields = line.split('\t')
        if len(fields) >= 2:
            repos.add(fields[1].strip().lower())
    return repos


def install_extensions():
    """Install any missing gh extensions. Returns True if all are present."""
    present = installed_extensions()
    ok = True
    for repo in EXTENSIONS:
        if repo.lower() in present:
            success(f"gh extension {repo} already installed")
            continue
        info(f"Installing gh extension {repo}...")
        try:
            run_cmd(['gh', 'extension', 'install', repo])
            success(f"gh extension {repo} installed")
        except subprocess.CalledProcessError:
            warn(f"Failed to install gh extension {repo}")
            ok = False
    return ok


def main():
    parse_dry_run()
    info("Installing GitHub CLI...")

    if not ensure_package(
        'GitHub CLI', brew='gh', pacman='github-cli', apt='gh', command='gh'
    ):
        return 1

    install_extensions()
    return 0


if __name__ == '__main__':
    sys.exit(main())
