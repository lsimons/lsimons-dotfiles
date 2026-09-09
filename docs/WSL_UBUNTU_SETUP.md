# WSL2 + Ubuntu support — working notes

Status: **in progress** on branch `feat/wsl-support` (stacked on
`feat/linux-support`, rebased onto `main`). Started 2026-09-09.

## Goal

Make these dotfiles install and work inside **WSL2 Ubuntu 24.04** on a Windows
11 host that was itself set up with [`windows/`](../windows/README.md). Ubuntu
(not Arch) because it is the most common WSL distro among colleagues at work.
Two uses drive this:

1. Run Claude Code with `/sandbox` (bubblewrap). Windows-native `claude.exe`
   cannot sandbox. Both `/sandbox` and
   [claude-docker](https://github.com/schubergphilis/claude-docker) are
   endorsed at work; teams pick either. We want to test both.
2. Carry the macOS/Linux dotfiles config over to WSL, so the WSL shell feels
   like the Mac.

## State of the machine (poppy)

- Windows 11 Pro x64, bootstrapped with `windows/` phases 1–3 as **Leo, not the
  bot** (see "Personal machine variant" in `windows/README.md`).
- WSL2 `Ubuntu-24.04`, systemd running, `bwrap`/`socat`/`rg` installed,
  `claude` installed via the native installer at `~/.local/bin/claude`,
  logged in, **`/sandbox` enabled and working**.
- Repo cloned on the Linux FS at `~/git/lsimons/lsimons-dotfiles`.
- Ubuntu Python is **3.12.3**. `script/install.py --dry-run` runs on it (the
  version guard passes), so the entry point is fine; individual topics that
  need 3.13/3.14 syntax are still to be discovered.

## What `feat/linux-support` gives us and where it stops

The branch adds a platform layer that is **Arch/Omarchy only**:

- `script/helpers.py`: `IS_LINUX`, `IS_ARCH` (from `/etc/os-release`
  `ID`/`ID_LIKE`), `is_omarchy()`, `pacman_*` helpers, and
  `ensure_package(label, brew=, cask=, pacman=, aur=, command=, optional=)`,
  the single choke point every topic uses (26 call sites, none call a
  package manager directly).
- `script/install.py`: `check_platform()`, `bootstrap_platform()` →
  `bootstrap_linux()` (pacman prerequisites + yay), per-topic `platforms.txt`.
- `ssh/install.py`: writes `~/.ssh/config.agent` with `IdentityAgent`
  pointing at the **Linux 1Password desktop app** socket
  (`~/.1password/agent.sock`). `1password/install.py` writes `agent.toml`
  for that app.

First dry-run on Ubuntu (2026-09-09) output, in order:

1. `[ERROR] No machine config for hostname 'poppy'`: enrollment needed.
2. `[WARN] This is Linux, but not an Arch derivative`: expected.
3. `1password` topic fails (exit 1) because of (1); nothing further ran.

## Plan

### 0. Enroll `poppy` (`machines/poppy.json`)

Blocker for everything else. Decide which identity this WSL is: personal
(`paddo.json` shape: Private vault, `my.1password.eu`) or work
(`sbplt2mkg3xk6.json` shape). Likely personal, mirroring the Windows side.
Needs `git.user.signingkey`, `ssh.aiKey`, `ssh.keys[]` with `op_vault` /
`op_account` / fingerprints. Copy from `paddo.json` and adjust.

### 1. Debian/Ubuntu package backend (`script/helpers.py`, `script/install.py`)

- `IS_DEBIAN = IS_LINUX and bool({"debian", "ubuntu"} & LINUX_DISTRO_IDS)`.
- `IS_WSL` from `WSL_DISTRO_NAME` env or `microsoft` in `/proc/version`.
- `ensure_package(..., apt=None)`; `apt_is_installed` via `dpkg-query -W`,
  `apt_install` via `sudo apt-get install -y --no-install-recommends`.
  Route `_linux_install` on `IS_ARCH` / `IS_DEBIAN`, not bare `IS_LINUX`.
- `bootstrap_linux()`: apt branch. `apt-get update`, prerequisites
  (`git curl ca-certificates gnupg build-essential`), and third-party apt
  repos only where apt is the right tool: 1Password CLI, GitHub CLI (Ubuntu's
  own `gh` is stale).
- `bootstrap_platform()`: Arch returns `sys.executable`; Ubuntu 24.04 ships
  3.12 so this probably needs to install a newer interpreter (deadsnakes PPA
  or `uv python install`) if any topic turns out to need 3.13+. Verify first;
  don't add it speculatively.

### 2. Package mapping

Ubuntu apt is old or missing for most of the CLI list (`mise`, `uv`, `herdr`,
`glab`, `pastel`, `aws-cli-v2`, `azure-cli`, `codex`, `copilot`). Policy:

- `apt=` only for what apt does well: `git`, `git-lfs`, `zsh`, `tmux`, `jq`,
  `docker` (docker-ce repo).
- Everything else via **mise** (`mise use -g`) or the vendor installer. Same
  pattern `windows/bootstrap-phase3.ps1` already uses. Check the mise
  registry per tool before deciding.
- Mark GUI/desktop topics `optional=True` or skip via `platforms.txt` on WSL.

### 3. WSL-specific behaviour

- Skip desktop topics when `IS_WSL`: `zed`, `ghostty`, `vivaldi`, `fonts`,
  `1password` desktop app, `omarchy`, `dock`. The Windows host owns those.
  Either a `platforms.txt` value distinguishing `linux` from `linux-desktop`,
  or an `IS_WSL` gate in `check_platform()`. Prefer whichever keeps
  `platforms.txt` declarative.
- `1password/`: install only `op` CLI. For desktop-app integration (biometric
  unlock) the Linux `op` cannot talk to the Windows app; alias `op` to
  `op.exe` (on PATH via `/mnt/c/...` interop) when `IS_WSL`. Affects
  `op_read_command()` and `ssh/install.py:op_write_secret()`.
  `agent.toml` is dead config on WSL; skip or warn.
- `ssh/`: third `OP_AGENT_SOCKET` branch. The Windows 1Password app exposes
  its agent on the named pipe `\\.\pipe\openssh-ssh-agent`. Bridge options:
  1. `npiperelay.exe` (Windows, add to `windows/scoopfile.json`) + `socat`
     (Linux, already installed for `/sandbox`) as a **systemd user unit**
     creating `$XDG_RUNTIME_DIR/1password-agent.sock`. Preferred: keeps
     Linux `ssh`/`git` unchanged.
  2. `core.sshCommand` / `GIT_SSH` → Windows `ssh.exe`. Simplest, but leaks
     Windows OpenSSH into every git op.
  3. `wsl2-ssh-pageant` / `wsl-ssh-agent`. Third-party; check maintenance.
- `sh/settings.sh` and shell topics: `SSH_AUTH_SOCK` must point at the bridged
  socket on WSL.

### 4. CI

`.github/workflows/ci.yml` already runs on an Ubuntu runner in dry-run mode.
Once `IS_DEBIAN` exists it can run a real install of a few cheap topics
(`jq`, `tmux`, `zsh`), which is a real coverage gain over dry-run only.

### 5. Docs

- `README.md`: platform matrix (macOS / Arch+Omarchy / Ubuntu+WSL).
- `windows/README.md`: a "WSL2" section pointing here; `npiperelay` in the
  scoop manifest.
- Fold these notes into proper docs when done; delete this file.

## Suggested order

1. `machines/poppy.json`, then re-run `python3 script/install.py --dry-run`
   until it gets through every topic in dry-run.
2. `IS_DEBIAN` + `apt=` backend + `bootstrap_linux()` apt branch. Real
   (non-dry) install of `jq`, `tmux`, `zsh`, `git` topics as the smoke test.
3. Package mapping topic by topic, mise-first.
4. WSL gating of desktop topics.
5. 1Password agent bridge.
6. CI + docs.

Commit small; each step should leave `--dry-run` green on Ubuntu and on macOS
(run the pytest suite: `tests/test_platform_layer.py` etc. cover the helpers).

## Open questions for Leo

- Identity for `poppy.json`: personal keys (as Windows side) or work?
- Is Omarchy/Arch support to be kept first-class alongside Ubuntu, or does
  Ubuntu become the primary Linux target? Affects how much `IS_ARCH` gating
  we keep testing.
- claude-docker test: Docker Desktop (licence at work?) vs Podman in WSL.
