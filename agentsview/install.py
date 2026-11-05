#!/usr/bin/env python3
"""Installation script for AgentsView (https://www.agentsview.io)

Local-first browser for past AI coding-agent sessions (Claude Code, Codex,
Gemini, OpenCode, Copilot, ...), with search and cost tracking. Run
`agentsview` (or `agentsview daemon start`) for the web UI on
http://127.0.0.1:8080.

- macOS: the Homebrew cask, which ships the desktop app and links the
  `agentsview` CLI.
- Arch: the AUR's agentsview-bin (CLI, x86_64 and aarch64).
- Debian/Ubuntu (incl. WSL): no native package; mise's github backend
  installs the linux amd64/arm64 CLI tarball from upstream's releases.

Windows has only a release MSI (no winget or scoop package), so it is not
covered by windows/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import ensure_package, info, parse_dry_run

MISE_TOOL = "github:kenn-io/agentsview"


def main():
    parse_dry_run()
    info("Installing AgentsView...")

    if not ensure_package(
        "AgentsView",
        brew="agentsview",
        cask=True,
        aur="agentsview-bin",
        mise=MISE_TOOL,
        command="agentsview",
        macos_app="AgentsView",
    ):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
