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
- Enrolled as `machines/poppy.json` (personal profile, same keys as
  `paddo.json`). `mise` installed via `https://mise.run` into
  `~/.local/bin`, `mise trust` + `mise install` done, so `mise run check`
  works and passes.
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

### 0. Enroll `poppy` (`machines/poppy.json`) — done

Personal identity (Private vault, `my.1password.eu`), a copy of
`paddo.json`. With it in place `script/install.py --dry-run` gets through
every topic on Ubuntu; the only platform noise left is the "not an Arch
derivative" warning from `check_platform()`, which step 1 removes.

### 1. Debian/Ubuntu package backend — code done, real install pending

Landed in `script/helpers.py` / `script/install.py`:

- `IS_DEBIAN` (from `ID`/`ID_LIKE`), `IS_WSL` (`WSL_DISTRO_NAME` or
  `microsoft` in `/proc/version`).
- `ensure_package(..., apt=, mise=)`. Routing is `IS_MACOS`+brew →
  `IS_ARCH`+pacman/aur → `IS_DEBIAN`+apt → `mise` fallback → "no package".
  `apt_is_installed` via `dpkg-query -W`, `apt_install` via
  `sudo apt-get install -y --no-install-recommends`.
- `bootstrap_linux()` dispatches to `bootstrap_arch()` / `bootstrap_debian()`.
  The Debian branch installs `build-essential git curl ca-certificates gnupg
  python3` and configures three vendor apt repositories (keyring under
  `/etc/apt/keyrings`, one `.list` each, `apt-get update` only when something
  changed): **mise** (`mise.jdx.dev/deb`), **GitHub CLI**
  (`cli.github.com/packages`) and **1Password** (incl. its debsig policy).
  mise via apt rather than `curl https://mise.run` so one mechanism covers all
  three and upgrades ride `apt upgrade`; `mise self-update` is disabled for
  package installs, which is fine.
- Python: Ubuntu 24.04's 3.12 clears the guard and every topic imports on it;
  no newer interpreter is installed.

### 2. Package mapping — done at the call sites

- `apt=`: git, git-lfs, git-filter-repo, zsh, tmux, jq, python3, ansible,
  ansible-lint, yamllint, docker.io / docker-compose-v2 / docker-buildx,
  fonts-cascadia-code, fonts-jetbrains-mono, and from the vendor repos mise,
  gh, 1password, 1password-cli.
- `mise=`: herdr, glab, pastel, uv, aws-cli, saml2aws, azure-cli (pipx
  backend; `azure/dependencies.txt` = `uv`), codex, copilot, opencode,
  topgrade, tfenv, `github:nicosuave/memex` (no registry entry; upstream
  ships linux tarballs). Each such topic now lists `mise` in
  `dependencies.txt` so `minimum_release_age` is configured first.
- powerlevel10k: no Ubuntu package. `oh-my-zsh/install.py` clones upstream
  into `$XDG_DATA_HOME/powerlevel10k` when no packaged theme is found;
  `powerline10k.zsh` searches that path too.
- Left as `optional` warnings on Debian (no package, desktop, or WSL-irrelevant):
  Ghostty, Zed, Vivaldi, Quarto, Iosevka, Lilex (now optional everywhere),
  Git Credential Manager, claude-history.
- Still to verify for real, not just dry-run: the mise `github:` backend
  picking the right memex asset, `pipx:azure-cli` through uv, and whether
  `tfenv` from mise behaves like the brew/AUR one.

### 3. WSL-specific behaviour

- Desktop topics: **done**. `platforms.txt` gained a `linux-desktop` value
  (a Linux with its own graphical session); `HOST_PLATFORMS` in
  `helpers.py` includes it on Linux unless `IS_WSL`. `zed`, `ghostty`,
  `vivaldi`, `fonts` now list `macos` + `linux-desktop`, `omarchy` lists
  `linux-desktop`, so all five are skipped under WSL (`dock` was macOS-only
  already). `1password/install.py` skips the app and `agent.toml` when
  `IS_WSL` and installs only the CLI; that is the one `IS_WSL` gate inside a
  topic, because the CLI is still wanted there.
- `1password/`: install only `op` CLI (done, see above). For desktop-app integration (biometric
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

1. ~~`machines/poppy.json`, then re-run `python3 script/install.py --dry-run`
   until it gets through every topic in dry-run.~~ Done 2026-09-09.
2. `IS_DEBIAN` + `apt=` backend + `bootstrap_linux()` apt branch: **code
   landed 2026-09-09** (dry-run green on Ubuntu, 122 unit tests). Real
   (non-dry) install of `jq`, `tmux`, `zsh`, `git` topics as the smoke test:
   pending (needs sudo).
3. Package mapping topic by topic, mise-first.
4. WSL gating of desktop topics: **done 2026-09-09**.
5. 1Password agent bridge.
6. CI + docs.

Commit small; each step should leave `--dry-run` green on Ubuntu and on macOS
(run the pytest suite: `tests/test_platform_layer.py` etc. cover the helpers).

## Decisions (Leo, 2026-09-09)

- **Identity for `poppy.json`:** personal keys, like `paddo`.
- **Platform matrix:** Omarchy/Arch, Ubuntu and WSL are all wanted, and
  Arch/Omarchy stays first-class. WSL means **Ubuntu on WSL only**; there is
  no interest in Omarchy/Arch on WSL, so `IS_WSL` gating only has to be
  exercised together with `IS_DEBIAN`.
- **claude-docker runtime:** no Docker Desktop licence. Test with a free /
  open-source runtime such as Podman inside WSL (Docker Engine in WSL with
  systemd is the other free option).
