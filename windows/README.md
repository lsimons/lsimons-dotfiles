# windows/

Windows 11 bootstrap. Written for the ARM64 AI-agent sandbox VM (UTM on
Apple Silicon); verified to also work unchanged on an x64 workstation — see
[Personal machine variant](#personal-machine-variant).

For the rationale (why native-only, why these tools, constraints), see
[../docs/AGENT_WINDOWS_SETUP.md](../docs/AGENT_WINDOWS_SETUP.md).

## Files

| File | Purpose |
|---|---|
| `bootstrap-phase1.ps1` | Unattended setup: winget + Scoop + registry + profiles + Claude Code |
| `bootstrap-phase2.ps1` | Credential-coupled setup: SSH key + git signing + optional repo clones |
| `bootstrap-phase3.ps1` | mise-managed runtimes and CLI tools (node, python, go, rust, …) |
| `debloat.ps1` | Remove Win11 preinstalled bloat: OneDrive + personal (consumer) Teams |
| `paretosecurity-tune.ps1` | Make Pareto Security green on this VM: screensaver resume-password + disable the BitLocker check |
| `packages.winget.yaml` | Declarative winget manifest (GUI / MSI apps) |
| `scoopfile.json` | Declarative Scoop manifest (CLI toolchain) |
| `Microsoft.PowerShell_profile.ps1` | PowerShell profile (copied into `$PROFILE` paths) |
| `WindowsTerminal-settings.json` | Windows Terminal settings (copied into LocalState) |
| `Zed-settings.json` | Zed settings for this VM (copied into `%APPDATA%\Zed`; selects the LSD Warm theme) |

## Prereqs

- Fresh Windows 11 (ARM64 in UTM, or x64 on bare metal), local account, updates applied
- `winget --version` works
- You have a browser (Vivaldi) to complete OAuth flows

## Run

### Phase 0 — unblock the scripts (once)

Fresh Windows 11 blocks unsigned scripts by default, and any file extracted
from a downloaded ZIP carries a Mark-of-the-Web that makes `RemoteSigned`
refuse it too. Fix both in one shot from the `windows\` directory:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
Get-ChildItem -Recurse | Unblock-File
```

Or bypass per-invocation (no permanent policy change):

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap-phase1.ps1
```

If you `git clone` the repo instead of downloading a ZIP, the Mark-of-the-Web
doesn't apply and `Set-ExecutionPolicy RemoteSigned` alone is enough.

### Phase 1 — unattended

From a **non-admin** PowerShell (5.1 is fine; pwsh 7 installs during this phase):

```powershell
cd ~\git\lsimons-dotfiles\windows
.\bootstrap-phase1.ps1
```

Preview first with `-DryRun`. Useful flags when iterating:

```powershell
.\bootstrap-phase1.ps1 -DryRun
.\bootstrap-phase1.ps1 -SkipWinget
.\bootstrap-phase1.ps1 -SkipScoop
.\bootstrap-phase1.ps1 -SkipClaude
```

winget will prompt for UAC once when it needs to install a machine-wide
package (Git for Windows, Simplewall, PowerShell 7). That's expected.

### Manual steps (between phases)

These cannot be scripted:

1. Launch **Windows Terminal** once so its LocalState directory is created,
   then re-run `bootstrap-phase1.ps1` to drop the settings file in place.
2. Sign in to **1Password** (Secret Key + passkey). Enable the SSH agent:
   *Settings → Developer → Use the SSH agent*.
3. Sign in to **Vivaldi** with the bot account.
4. `gh auth login` — OAuth flow in the browser.
5. `claude` → `/login` — OAuth flow in the browser.
6. Run `.\paretosecurity-tune.ps1` to apply the two VM-specific fixes needed to
   reach green: the screensaver resume-password, and disabling the BitLocker
   check (no TPM on this VM). Then run **Pareto Security** and remediate any
   remaining checks. Both fixes are idempotent.
7. Configure **Simplewall** rules, then switch to alert mode.

### Phase 2 — credentials

From **pwsh 7** (`pwsh`), with 1Password signed in and CLI integration on:

```powershell
cd ~\git\lsimons-dotfiles\windows
.\bootstrap-phase2.ps1
```

Optional flags:

```powershell
.\bootstrap-phase2.ps1 -DryRun
.\bootstrap-phase2.ps1 -Repos @('lsimons/lsimons-dotfiles','lsimons/lsimons-arch')
.\bootstrap-phase2.ps1 -SshKeyItem 'op://Private/my ssh key/public key'
```

### Phase 3 — mise runtimes

```powershell
cd ~\git\lsimons-dotfiles\windows
.\bootstrap-phase3.ps1
```

Tools that are not yet available for Windows/ARM64 via mise will warn and be skipped.
On x64 they all install.

### Personal machine variant

The same scripts work on a real x64 workstation (verified 2026-09 on a fresh
Windows 11 Pro install). Everything in phases 1–3 runs unchanged; only the
identity-coupled manual steps differ:

- **Skip `paretosecurity-tune.ps1`.** A real machine has a TPM, so the
  BitLocker check applies — leave every Pareto check enabled and remediate
  until green.
- Sign in to Vivaldi, GitHub, Claude, and 1Password as **yourself**, not the bot.
- Run phase 2 with your own identity instead of the bot defaults, otherwise
  commits are authored as the bot and signed with the bot key:

  ```powershell
  .\bootstrap-phase2.ps1 `
    -SshKeyItem 'op://Private/<your ssh key item>/public key' `
    -GitName    'Leo Simons' `
    -GitEmail   'mail@leosimons.com'
  ```

  Phase 2 always writes the public key to `~\.ssh\id_lsimons_bot_ed25519.pub`
  regardless of which 1Password item it came from — the filename is
  misleading on a personal machine but the contents are your key. Runs of
  `git commit` and `git log --show-signature` in Verify below confirm which
  key is in use.

### Debloat (optional)

Remove the two apps Windows 11 auto-installs and pins for a personal account —
OneDrive and the **personal** ("Chat") Teams app. The work/school Teams client
(`Microsoft.Teams` under Program Files) is left untouched.

```powershell
cd ~\git\lsimons-dotfiles\windows
.\debloat.ps1 -DryRun     # preview
.\debloat.ps1             # per-user removal (run as admin to also deprovision)
```

The OneDrive step warns and pauses if Known Folder Move has redirected your
Desktop/Documents/Pictures into OneDrive — download those files locally first,
or you'll lose access to online-only copies.

### Keep tools up to date

`topgrade` (installed via Scoop) updates everything in one shot — Scoop packages,
winget packages, and mise-managed runtimes:

```powershell
topgrade
```

### Verify

```powershell
# Tools on PATH
git --version ; gh --version ; op --version ; claude --version ; scoop --version

# PowerShell profile loaded
$PROFILE.CurrentUserAllHosts

# Commit signing works
cd ~\git\lsimons-dotfiles
git commit --allow-empty -m 'test: signing'
git log --show-signature -1
```

## Idempotency

Re-running either phase is safe. Each step checks before acting. File writes
are hash-compared so unchanged files don't get rewritten.

## Caveats

- **No WSL2, no Docker, no Podman on the ARM64 VM.** Apple Silicon M2 doesn't
  expose nested virtualization, and even M3+ only exposes it for Linux guests.
  This VM cannot run WSL2 regardless of effort spent trying. Run a separate
  Linux UTM VM if you need containers. (Not a constraint on bare-metal x64,
  but the scripts don't install any of these either way.)
- **winget package IDs** may drift over time. If `winget configure` fails
  with "no package found", update the `id:` in `packages.winget.yaml`.
- **Scoop refuses to run as admin.** Phase 1 enforces this — it throws if
  started elevated.
- Windows Terminal settings file is **copied, not symlinked**. Windows
  symlinks need Developer Mode (admin to enable) so a copy is the simpler
  trade-off. Re-run phase 1 to resync after editing.
