#!/usr/bin/env python3
"""Generate per-repository coding-agent config from mise tasks and overrides.

For each directory given on the command line (or, if none, every sibling of
the repositories root that has a .mise.toml or Claude override), write:

* .claude/settings.json permissions for each mise task plus Claude overrides
* .codex/rules/mise.rules prefix rules for each mise task

Claude overrides live in overrides/claude/<repo-name>.json. Their
allow/deny/ask lists are merged with generated permissions and deduplicated.

The goal is to whitelist the specific task-runner invocations that exist in
each repo today, instead of blanket-approving `mise run` / `mise tasks run`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TASK_HEADER_RE = re.compile(r'^\[tasks\.(?:"([^"]+)"|([A-Za-z0-9_.:-]+))\]\s*$')


def parse_tasks(mise_toml: Path) -> list[str]:
    """Return the list of task names declared in a .mise.toml file."""
    tasks: list[str] = []
    for line in mise_toml.read_text().splitlines():
        m = TASK_HEADER_RE.match(line)
        if m:
            tasks.append(m.group(1) or m.group(2))
    return tasks


def dedupe(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_claude_settings(tasks: list[str], override: dict | None) -> dict:
    allow = [f"Bash(mise run {t})" for t in tasks] + [
        f"Bash(mise run {t} *)" for t in tasks
    ]
    deny: list[str] = []
    ask: list[str] = []
    if override:
        perms = override.get("permissions", {})
        allow += list(perms.get("allow", []))
        deny += list(perms.get("deny", []))
        ask += list(perms.get("ask", []))

    perms_out: dict[str, list[str]] = {}
    if allow:
        perms_out["allow"] = dedupe(allow)
    if deny:
        perms_out["deny"] = dedupe(deny)
    if ask:
        perms_out["ask"] = dedupe(ask)
    return {"permissions": perms_out}


def build_codex_rules(tasks: list[str]) -> str:
    """Return Codex prefix rules for the given mise task names."""
    lines = [
        'prefix_rule(pattern = ["mise", "run", '
        f'{json.dumps(task)}], decision = "allow")'
        for task in tasks
    ]
    return "\n".join(lines) + ("\n" if lines else "")


DOTFILES_REPO = Path(__file__).resolve().parents[1]


def write_generated(target: Path, rendered: str, dry_run: bool) -> None:
    """Write or remove one generated config file."""
    if dry_run:
        if rendered:
            print(f"--- {target} ---")
            print(rendered, end="")
        elif target.exists():
            print(f"would remove: {target}")
        return

    if not rendered:
        if target.exists():
            target.unlink()
            print(f"removed:   {target}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text() if target.exists() else None
    if existing == rendered:
        print(f"unchanged: {target}")
    else:
        target.write_text(rendered)
        print(f"wrote:     {target}")


def sync_repo(repo: Path, claude_overrides_dir: Path, dry_run: bool) -> bool:
    # This repository maintains its native agent config by hand.
    if repo.resolve() == DOTFILES_REPO:
        return False

    mise_toml = repo / ".mise.toml"
    override_file = claude_overrides_dir / f"{repo.name}.json"

    if not mise_toml.exists() and not override_file.exists():
        return False

    tasks = parse_tasks(mise_toml) if mise_toml.exists() else []
    override = json.loads(override_file.read_text()) if override_file.exists() else None

    claude_settings = build_claude_settings(tasks, override)
    claude_rendered = (
        json.dumps(claude_settings, indent=2) + "\n"
        if claude_settings["permissions"]
        else ""
    )
    write_generated(repo / ".claude" / "settings.json", claude_rendered, dry_run)
    write_generated(
        repo / ".codex" / "rules" / "mise.rules",
        build_codex_rules(tasks),
        dry_run,
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repos-dir",
        type=Path,
        default=Path.home() / "git" / "lsimons",
        help="Directory containing sibling repos (default: ~/git/lsimons)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without changing any files",
    )
    parser.add_argument(
        "repos",
        nargs="*",
        type=Path,
        help=(
            "Specific repo paths to sync; default is every sibling with a "
            ".mise.toml or override"
        ),
    )
    args = parser.parse_args()

    claude_overrides_dir = Path(__file__).resolve().parent / "overrides" / "claude"

    if args.repos:
        candidates = [p.resolve() for p in args.repos]
    else:
        if not args.repos_dir.is_dir():
            print(f"No such directory: {args.repos_dir}", file=sys.stderr)
            return 1
        candidates = sorted(p for p in args.repos_dir.iterdir() if p.is_dir())

    touched = 0
    for repo in candidates:
        if sync_repo(repo, claude_overrides_dir, args.dry_run):
            touched += 1

    if touched == 0:
        print("No repositories had a .mise.toml or matching override.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
