#!/usr/bin/env python3
"""Migrate from per-language version managers to mise.

This is a one-shot, opt-in script. Run it BEFORE `./script/install.py`
after updating the dotfiles repo to the mise-based layout.

What it does:
  1. Backs up per-language version manager state directories (nvm,
     rustup, cargo, pyenv, rbenv, goenv, nodenv) to
     ~/.dotfiles-backup/migrate-to-mise/<timestamp>/.
  2. Optionally uninstalls Homebrew formulae that mise now owns
     (node, nvm, go, ruby) -- interactive per-formula prompt.

What it does NOT do:
  - It does NOT touch Homebrew-installed Python. The `python/` topic's
    install.py intentionally keeps `python@3` (the current-stable Brew
    cask) installed alongside mise's Python, because other Brew formulae
    depend on it and because it's the bootstrap interpreter for
    install.py itself. `--aggressive-brew` is still offered for cleaning
    up *old* versioned Python formulae (`python@3.12`, `python@3.13`);
    `python@3` itself is never in the uninstall list.
  - It does NOT install anything. Run ./script/install.py after.

Usage:
    python3 scripts/migrate.py            # interactive
    python3 scripts/migrate.py --dry-run  # show plan only
    python3 scripts/migrate.py --yes      # skip confirmation (backups
                                          # still happen; brew uninstall
                                          # is still gated separately)
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import info, success, error


HOME = Path.home()
XDG_DATA_HOME = Path(os.environ.get('XDG_DATA_HOME', HOME / '.local/share'))

# Directories to back up, keyed by short label.
BACKUP_TARGETS = {
    'nvm': XDG_DATA_HOME / 'nvm',
    'rustup': XDG_DATA_HOME / 'rustup',
    'cargo': XDG_DATA_HOME / 'cargo',
    'pyenv': HOME / '.pyenv',
    'rbenv': HOME / '.rbenv',
    'goenv': HOME / '.goenv',
    'nodenv': HOME / '.nodenv',
    # NVM's historical default location (not XDG):
    'nvm-home': HOME / '.nvm',
}

# Homebrew formulae that mise replaces. Offered interactively.
# `python@3` deliberately NOT in the aggressive list: the python/ topic
# installs it on purpose (see python/install.py).
BREW_CANDIDATES_SAFE = ['node', 'nvm', 'go', 'ruby']
BREW_CANDIDATES_AGGRESSIVE = ['python@3.12', 'python@3.13']


def run(cmd, check=True, capture_output=False):
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=True,
    )


def prompt_yes_no(question, default_no=True):
    suffix = ' [y/N]: ' if default_no else ' [Y/n]: '
    ans = input(question + suffix).strip().lower()
    if not ans:
        return not default_no
    return ans in ('y', 'yes')


def collect_backup_plan():
    """Return list of (label, path) for directories that actually exist."""
    return [(label, path) for label, path in BACKUP_TARGETS.items()
            if path.exists() or path.is_symlink()]


def collect_brew_plan(aggressive=False):
    """Return list of brew formulae present on this system that we'd remove."""
    try:
        result = run(['brew', 'list', '--formula', '-1'],
                     capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    installed = set(result.stdout.split())
    candidates = list(BREW_CANDIDATES_SAFE)
    if aggressive:
        candidates += BREW_CANDIDATES_AGGRESSIVE
    return [f for f in candidates if f in installed]


def print_plan(backup_plan, brew_plan, backup_dir):
    print()
    print('Migration plan')
    print('=' * 60)
    print(f'Backup directory: {backup_dir}')
    print()
    if backup_plan:
        print('The following directories will be MOVED to the backup:')
        for label, path in backup_plan:
            print(f'  - {label:<10} {path}')
    else:
        print('No per-language version manager directories found to back up.')
    print()
    if brew_plan:
        print('The following Homebrew formulae are installed and will be')
        print('OFFERED for uninstall (separate prompt):')
        for formula in brew_plan:
            print(f'  - {formula}')
    else:
        print('No Homebrew formulae flagged for uninstall.')
    print('=' * 60)
    print()


def do_backups(backup_plan, backup_dir, dry_run):
    if not backup_plan:
        return

    if dry_run:
        info(f"[dry-run] Would create {backup_dir}")
    else:
        backup_dir.mkdir(parents=True, exist_ok=True)

    for label, path in backup_plan:
        dest = backup_dir / label
        if dry_run:
            info(f"[dry-run] Would move {path} -> {dest}")
            continue

        try:
            shutil.move(str(path), str(dest))
            success(f"Moved {path} -> {dest}")
        except Exception as exc:
            error(f"Failed to move {path}: {exc}")


def do_brew_uninstalls(brew_plan, dry_run):
    if not brew_plan:
        return

    print()
    if dry_run:
        for formula in brew_plan:
            info(f"[dry-run] Would prompt to uninstall brew formula "
                 f"'{formula}'")
        return

    info("Homebrew uninstall prompts follow. Decline any you still want.")
    for formula in brew_plan:
        if not prompt_yes_no(f"Uninstall brew formula '{formula}'?"):
            info(f"Skipping {formula}")
            continue

        try:
            run(['brew', 'uninstall', '--ignore-dependencies', formula])
            success(f"Uninstalled {formula}")
        except subprocess.CalledProcessError:
            error(f"Failed to uninstall {formula} (leaving in place)")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--dry-run', action='store_true',
                        help='Print the plan without making changes.')
    parser.add_argument('--yes', action='store_true',
                        help='Skip the confirmation prompt for backups. '
                             'Brew uninstall is still gated per-formula.')
    parser.add_argument('--aggressive-brew', action='store_true',
                        help='Also offer to uninstall Homebrew Python '
                             '(risky: breaks the bootstrap interpreter '
                             'until you rerun install.py).')
    args = parser.parse_args(argv)

    info('lsimons-dotfiles: migrate to mise')
    info('=' * 60)

    backup_plan = collect_backup_plan()
    brew_plan = collect_brew_plan(aggressive=args.aggressive_brew)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = HOME / '.dotfiles-backup' / 'migrate-to-mise' / timestamp

    print_plan(backup_plan, brew_plan, backup_dir)

    if not backup_plan and not brew_plan:
        success("Nothing to migrate. You're already clean.")
        return 0

    if args.dry_run:
        info('Dry-run mode: no changes made.')
    elif not args.yes:
        if not prompt_yes_no("Proceed with the backup step?"):
            info('Aborted. No changes made.')
            return 1

    do_backups(backup_plan, backup_dir, args.dry_run)
    do_brew_uninstalls(brew_plan, args.dry_run)

    print()
    success("Migration step complete.")
    info("Next: run ./script/install.py to install mise + topics.")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        error('Cancelled by user')
        sys.exit(130)
