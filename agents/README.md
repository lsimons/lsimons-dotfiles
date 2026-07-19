# Coding agents

This directory is the shared source of truth for coding-agent configuration:

- `AGENTS.md` contains global instructions.
- `shared.py` owns shared paths, attribution policy, and instruction rendering.
- `skills/` contains skills linked into each supported agent's config directory.
- `overrides/<agent>/` contains agent-specific per-repository additions.
- `sync-repo-config.py` generates native per-repository configuration from
  tasks declared in `.mise.toml`.

Preview configuration for every repository under `~/git/lsimons`:

```sh
python3 agents/sync-repo-config.py --dry-run
```

Pass repository paths to sync only those repositories. The generated files are
`.claude/settings.json`, `.codex/rules/mise.rules`, and
`.opencode/opencode.json`.
