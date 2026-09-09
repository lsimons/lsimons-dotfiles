# lsimons-dotfiles

Homedir setup for @lsimons (and @lsimons-bot)

A modular dotfiles configuration for macOS, Arch-based Linux ([Omarchy](https://omarchy.org/)) and Ubuntu (including under WSL2), featuring ZSH and Bash support, XDG Base Directory compliance, and 1Password CLI integration for secure secret management.

## Features

- **Modular topic-based structure** - Inspired by [holman/dotfiles](https://github.com/holman/dotfiles)
- **XDG Base Directory compliant** - Follows the [freedesktop.org specification](https://specifications.freedesktop.org/basedir-spec/latest/)
- **1Password integration** - Load secrets securely without storing them in git
- **ZSH configuration** - Clean, modular ZSH setup with Oh My Zsh
- **Bash configuration** - Modular Bash setup with the same topic-based loading
- **Python-based installation** - Idempotent installation automation
- **Cross-platform packaging** - One package name per platform: Homebrew
  on macOS, pacman/yay on Arch, apt on Ubuntu with mise filling the gaps
  in its archive. Topics that only make sense on one platform declare it
  in a `platforms.txt` and are skipped elsewhere
- **Development tools** - Includes editors, terminals, CLI tools, and coding agents

## Quick Start

For a fresh VM setup (UTM, Little Snitch, accounts), see [AGENT_SETUP.md](./docs/AGENT_SETUP.md) first.
For the Windows 11 ARM64 sandbox variant, see [AGENT_WINDOWS_SETUP.md](./docs/AGENT_WINDOWS_SETUP.md) and [windows/README.md](./windows/README.md).

On an existing macOS system with Homebrew, an Arch-based Linux (Omarchy)
system, or an Ubuntu system (a WSL2 distro included):

```bash
mkdir -p ~/git/lsimons && cd ~/git/lsimons
git clone https://github.com/lsimons/lsimons-dotfiles.git
cd lsimons-dotfiles
./script/install.py              # preview first: ./script/install.py --dry-run
source ~/.zshrc
```

The installer needs **Python 3.11 or newer**. macOS only ships 3.9 in
the Command Line Tools, so on a fresh Mac run `brew install python`
first; the installer says so and stops if the interpreter is too old.
Arch is a rolling release, so its `python` is always new enough, and
Ubuntu 24.04's `python3` (3.12) is new enough too.

Installing packages needs root on Linux, so `sudo` may ask for your
password once — the same way a Homebrew cask does on macOS.

Once mise is installed you can also use `mise run install` (add
`-- --dry-run` to preview) and `mise run check` for subsequent runs.

Run `mise run check` (or `python3 script/check.py`) to validate the
repo without touching your system — this is what CI runs on every push.
Prefer `mise run check`: it provisions ruff, shellcheck and actionlint
from `.mise.toml`'s `[tools]` section at exactly the versions CI uses.
The bare `check.py` entry point fails, rather than skipping, when those
tools are not on PATH.

`mise run ci` runs everything CI runs — `check` plus the zizmor
workflow audit — and `mise run ci-watch` follows the real run on GitHub.

## What Gets Installed

The installation script (`./script/install.py`) will:

1. **Bootstrap the package manager** — Homebrew plus `python@3` on macOS;
   the `base-devel`/`git`/`python` prerequisites plus `yay` on Arch; on
   Ubuntu the build prerequisites plus the vendor apt repositories for
   mise, GitHub CLI and 1Password, which Ubuntu's own archive lacks or
   ships stale
2. **Create `~/.dotfiles` symlink** pointing to this repository
3. **Set up XDG directories** (`~/.config`, `~/.local/share`, `~/.cache`, `~/.local/state`)
4. **Symlink dotfiles** to appropriate locations
5. **Run topic installers** for development tools, skipping any whose
   `platforms.txt` excludes the current platform:

| Topic | Installs |
|-------|----------|
| `1password/` | 1Password app and CLI (`op`). Under WSL: no app, but a systemd user service bridging the Windows app's SSH agent into `~/.1password/agent.sock`, and `op` running the Windows `op.exe` |
| `agents/` | Shared coding-agent instructions, links to the [lsimons-skills](https://github.com/lsimons/lsimons-skills) collection, and repository config sync |
| `ansible/` | Ansible and related tools |
| `aws/` | AWS CLI (`awscli`) + default `~/.aws/config`; `saml2aws` configured with the Browser provider for Okta OIE |
| `azure/` | Azure CLI (`az`) |
| `bash/` | Bash configuration and directories |
| `bash-it/` | Bash-it framework (prompt, plugins) |
| `claude/` | Claude Code CLI and configuration |
| `colors/` | `pastel` color CLI + docs for theme/palette files across tools |
| `codex/` | OpenAI Codex CLI and configuration |
| `copilot/` | GitHub Copilot CLI (git-config-ai routing) |
| `docker/` | Rancher Desktop on macOS; the docker engine, compose and buildx on Linux |
| `dock/` | Pins apps to the macOS Dock via dockutil (runs last). **macOS only** |
| `gemini/` | Gemini CLI |
| `fnox/` | fnox (1Password secret injection, via mise) |
| `fonts/` | Fonts (Cascadia Code, Iosevka, JetBrains Mono, Lilex, Lilex Nerd Font). **Desktop only** |
| `gh/` | GitHub CLI + extensions (`gh stack`) |
| `glab/` | GitLab CLI (`glab`) |
| `go/` | Go (via mise) |
| `ghostty/` | Ghostty terminal (no aarch64 Linux build — config only there) |
| `git/` | Git + credential helper (Git Credential Manager where packaged, else `gh auth git-credential`), git-filter-repo, Git LFS (installed and initialized) |
| `herdr/` | herdr terminal agent multiplexer + LSD Warm Light theme |
| `jdk/` | OpenJDK (via mise) |
| `jq/` | jq JSON processor (used by the Claude statusline) |
| `lsimons-agent/` | LLM agent environment configuration |
| `memex/` | memex agent-transcript search + its herdr plugin |
| `mise/` | mise (polyglot tool version manager) |
| `node/` | Node.js (via mise) + pnpm (via corepack) |
| `oh-my-zsh/` | Oh My Zsh + powerlevel10k |
| `omarchy/` | LSD Warm Dark/Light Omarchy themes, an extra Hyprland keybinding layer, and Omarchy's default-app selection. **Linux only** |
| `opencode/` | OpenCode CLI (permissions, model variants, LSD Warm theme, git-config-ai routing) |
| `openspec/` | openspec |
| `pi-coding-agent/` | pi-coding-agent (settings, LSD Warm themes, git-config-ai routing) |
| `python/` | Python (via mise) + XDG config |
| `quarto/` | Quarto (Homebrew cask; `quarto-cli-bin` from the AUR) |
| `ruby/` | Ruby (via mise) |
| `rust/` | Rust (via mise) + CARGO_HOME |
| `sh/` | Shared shell configuration (PATH, XDG, settings) |
| `ssh/` | SSH configuration (post-quantum warning, 1Password agent) |
| `swiftdialog/` | swiftDialog (via Homebrew cask; skipped if already present, e.g. via MDM). **macOS only** |
| `terminal/` | macOS Terminal.app "LSD Warm Light" profile (mirrors Ghostty). **macOS only** |
| `terraform/` | tfenv and Terraform |
| `timeout/` | `timeout` command for macOS (via the `aisk/tap` Homebrew tap). **macOS only** — Linux coreutils already has it |
| `tmux/` | tmux |
| `topgrade/` | topgrade (automated updates) |
| `uv/` | uv (Python package manager) |
| `vivaldi/` | Vivaldi Browser (no aarch64 Linux build) |
| `wordpress/` | WordPress shell environment |
| `zed/` | Zed editor (`zeditor` on Linux; no aarch64 build — config only there) |
| `zsh/` | ZSH itself (Arch has no zsh by default) and its directories |

## For AI Agents

If you're an AI coding agent (GitHub Copilot, Claude Code, etc.) working on this repository, please read [AGENTS.md](AGENTS.md) for detailed instructions and guidelines.

## Structure

```
.
├── script/           # Installation scripts and helpers
│   ├── install.py    # Main installer (supports --dry-run)
│   ├── check.py      # Validation checks (py_compile, ruff, shellcheck, actionlint, JSON, tests, install dry-run)
│   └── helpers.py    # Shared functions for topic installers
├── machines/         # Machine-specific configuration
│   ├── default.json  # Default config (used when no hostname match)
│   └── <hostname>.json # Per-machine overrides
└── <topic>/          # One directory per topic (see table above)
```

### File Naming Convention

- `*.symlink` - Files symlinked to home directory or XDG directories
- `*.sh` - Shared shell config, sourced by both bash and zsh
- `*.zsh` - ZSH-specific config, sourced only by zsh
- `*.bash` - Bash-specific config, sourced only by bash
- `path.sh` / `path.zsh` / `path.bash` - Loaded first, for PATH configuration
- `completion.sh` / `completion.zsh` / `completion.bash` - Loaded last
- `install.py` - Topic-specific installation script
- `dependencies.txt` - Other topics that must install first, one per line
- `platforms.txt` - Platforms this topic supports, one per line: `macos`,
  `linux`, or `linux-desktop` for a Linux with a graphical session of its
  own (everything but WSL). Absent means every platform, which is the
  usual case

Loading order: shared and shell-specific `path.*` files first, ordinary shared
and shell-specific files second, then shared and shell-specific `completion.*`
files.

## Platform Support

| Platform | Packages from | Desktop topics | Notes |
|----------|---------------|----------------|-------|
| macOS | Homebrew | yes | |
| Arch-based Linux | pacman, yay for the AUR | yes | [Omarchy](https://omarchy.org/) in practice; its config tree is what the `omarchy/` topic detects. Derivatives are recognised through `ID_LIKE` in `/etc/os-release`, so Arch Linux ARM counts too |
| Ubuntu / Debian | apt, mise for the rest | on a desktop | Ubuntu's archive has no mise or 1Password CLI and a stale gh; the bootstrap adds the vendors' apt repositories for those |
| Ubuntu under WSL2 | apt, mise for the rest | no | The Windows host owns editor, browser, fonts and the 1Password app; the `1password/` topic bridges the Windows app's SSH agent and CLI into WSL. See [docs/WSL_UBUNTU_SETUP.md](./docs/WSL_UBUNTU_SETUP.md) and [windows/README.md](./windows/README.md) |

Topic installers should not branch on the platform themselves. Call
`ensure_package()` from `script/helpers.py` with a package name per
platform, and let it pick the manager:

```python
ensure_package("GitHub CLI", brew="gh", pacman="github-cli", apt="gh", command="gh")
ensure_package("topgrade", brew="topgrade", aur="topgrade", mise="topgrade",
               command="topgrade")
ensure_package("Ghostty", brew="ghostty", cask=True, pacman="ghostty",
               command="ghostty", optional=True)
```

`command=` (or `macos_app=`) is the presence probe. `apt=` is for what
Debian and Ubuntu package well; `mise=` names a tool in the mise
registry (or a `github:owner/repo` release) and is the fallback wherever
no native name is given, which on Ubuntu is most developer CLIs.
`optional=True` turns "no package for this platform" and "the install
failed" into warnings, which is how the topics for software with no
aarch64 Linux build — Ghostty, Zed, Vivaldi, Quarto — avoid failing the
whole run.

Work that is genuinely platform-shaped, rather than just a different
package name, is the exception and does test `IS_MACOS` / `IS_LINUX` /
`IS_WSL`: the mise GUI PATH hook (a LaunchAgent vs. a systemd
`environment.d` drop-in), the 1Password SSH agent socket and its WSL
bridge, and the docker engine.

A whole topic that only belongs on one platform says so in a
`platforms.txt` instead; a desktop topic lists `linux-desktop` rather
than `linux` so it stays off WSL. `script/install.py` skips the others
and drops any dependency on a skipped topic.

## XDG Base Directory Compliance

This setup follows the XDG Base Directory specification:

| Variable | Default | Purpose |
|----------|---------|---------|
| XDG_CONFIG_HOME | ~/.config | Configuration files |
| XDG_DATA_HOME | ~/.local/share | Data files |
| XDG_CACHE_HOME | ~/.cache | Cache files |
| XDG_STATE_HOME | ~/.local/state | State files (logs, history) |

All tools are configured to respect these directories:
- ZSH history: `~/.local/state/zsh/history`
- Bash history: `~/.local/state/bash/history`
- Python history: `~/.local/state/python/history`
- Git config: `~/.config/git/config`
- mise installs/shims: `~/.local/share/mise/`

## Machine-Specific Configuration

The `machines/` directory contains per-machine configuration in JSON format. During installation, `get_machine_config()` in `helpers.py` loads `machines/<short-hostname>.json`, merging with `machines/default.json`.

**Every machine must be enrolled before installing.** `machines/default.json` intentionally has no SSH keys and no git signing key, so `get_machine_config()` refuses to fall back to it for a hostname with no dedicated file — the installer exits with an error instead of silently generating a git config with commit signing enabled but no signing key, or a 1Password SSH agent config with no exposed keys. To enroll a new machine, create `machines/<hostname>.json` (use `hostname -s` to get the short hostname) before running the installer.

### Provider credentials (`providers`)

Some tools (currently the Codex and OpenCode shell wrappers, see
`codex/codex.sh` and `opencode/opencode.sh`) need an LLM provider API key
that lives in 1Password under a different account on different machines
— e.g. the SBP work account on a work laptop, a personal account
elsewhere. This is configured per machine under `providers`, mirroring
the shape of the existing `ssh.keys[].op_account`/`op_vault` fields:

```json
{
  "providers": {
    "litellm": {
      "op_account": "schubergphilis",
      "op_ref": "op://Employee/litellm-pat/token"
    }
  }
}
```

- `op_account` is passed to `op read --account`.
- `op_ref` is a full `op://vault/item/field` reference.
- Only a reference is stored here, never the secret itself.

Resolution happens at **call time**: `codex()`/`opencode()` invoke
`script/provider_credential.py <provider>`, which reads the CURRENT
machine's config (via `get_machine_config()`/`get_provider_credential()`
in `helpers.py`) and prints the account/reference for `op read` to
consume. A machine with no `providers.<provider>` entry configured fails
closed — the wrapper returns a non-zero exit and an explicit error
instead of falling back to another machine's account or reference.

## 1Password Integration

Secrets are loaded from 1Password, not stored in git. See the [1Password topic](./1password).

## Customization

### Adding a New Topic

1. Create a directory:
   ```bash
   mkdir ~/.dotfiles/mytopic
   ```

2. Add files:
   - `mytopic.sh` - Shared shell config (auto-loaded in both bash and zsh)
   - `mytopic.zsh` - ZSH-specific config (optional)
   - `mytopic.bash` - Bash-specific config (optional)
   - `mytopic.symlink` - File to symlink
   - `install.py` - Installation script (optional)

3. Re-run installer:
   ```bash
   ~/.dotfiles/script/install.py
   ```

## Troubleshooting

### `ModuleNotFoundError: No module named 'tomllib'`

The installer needs Python 3.11 or newer, and macOS ships 3.9 in the
Command Line Tools. Install a newer Python and re-run:

```bash
brew install python              # macOS
sudo pacman -S python            # Arch
sudo apt-get install -y python3  # Debian/Ubuntu
./script/install.py
```

On a Mac with no Homebrew either, install Homebrew first (see
https://brew.sh). The installer does that itself normally, but it cannot
get that far on Python 3.9.

### A topic was skipped on Linux

Expected for `dock`, `terminal`, `swiftdialog` and `timeout`, and under
WSL also for `fonts`, `ghostty`, `omarchy`, `vivaldi` and `zed` — see
Platform Support above. The installer names every topic it skips and
why.

### Commit signing fails on Linux

Git signs through 1Password's `op-ssh-sign`, which needs the desktop app
running with the SSH agent enabled (Settings → Developer → Use the SSH
agent). `~/.ssh/config.agent`, generated by `ssh/install.py`, points ssh
at `~/.1password/agent.sock`.

Under WSL there is no `op-ssh-sign`; git signs with `ssh-keygen` through
the same socket, which the `1password-agent-bridge` systemd user service
provides from the Windows app. Check it with
`systemctl --user status 1password-agent-bridge` and
`SSH_AUTH_SOCK=~/.1password/agent.sock ssh-add -l`. It needs `npiperelay`
on the Windows side (`scoop install npiperelay`) and the SSH agent enabled
in the Windows 1Password app.

### XDG directories not created

Re-run installer:
```bash
~/.dotfiles/script/install.py
```

## Security

This is a personal project. Do not depend on it, and in particular do
not depend on its security. There is no support.

To report a vulnerability, use the "Report a vulnerability" button under
this repository's Security tab on GitHub.

## License

Apache License 2.0. See the [LICENSE](./LICENSE) file.

## Inspiration

- [holman/dotfiles](https://github.com/holman/dotfiles)
- [iheitlager/dotfiles](https://github.com/iheitlager/dotfiles)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/)
