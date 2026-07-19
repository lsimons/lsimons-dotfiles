#Requires -Version 5.1
<#
.SYNOPSIS
    Tune Pareto Security for this Windows 11 ARM64 VM so it reports green.

.DESCRIPTION
    Idempotent: re-running is safe. Two fixes, both reproducible:

      1. Require a password after the screensaver / on resume. This is the
         "Password after sleep or screensaver" Pareto check. It maps to the
         HKCU screensaver settings that the Screen Saver dialog's
         "On resume, display logon screen" checkbox writes.

      2. Disable the "Disk encryption is enabled" (BitLocker) Pareto check.
         This UTM VM on Apple Silicon has no TPM and runs Windows 11 Home,
         so BitLocker can't be enabled -- the check can never pass and is
         disabled rather than left permanently red.

    Run AFTER Pareto Security is installed (phase 1 installs it via winget).

    See ../docs/AGENT_WINDOWS_SETUP.md for rationale.

.PARAMETER DryRun
    Print what would happen without making changes.

.EXAMPLE
    PS> .\paretosecurity-tune.ps1
    PS> .\paretosecurity-tune.ps1 -DryRun
#>

[CmdletBinding()]
param(
  [switch]$DryRun,
  # Pareto check UUIDs to disable (can't pass on this VM).
  # c2cae85c... = "Disk encryption is enabled" (BitLocker; no TPM on the VM).
  [string[]]$DisableChecks = @('c2cae85c-0335-4708-a428-3a16fd407912')
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Info    { param($m) Write-Host "[INFO]    $m" -ForegroundColor Blue }
function Write-Step    { param($m) Write-Host "[STEP]    $m" -ForegroundColor Cyan }
function Write-Ok      { param($m) Write-Host "[OK]      $m" -ForegroundColor Green }
function Write-WarnMsg { param($m) Write-Host "[WARN]    $m" -ForegroundColor Yellow }
function Write-Dry     { param($m) Write-Host "[DRY-RUN] $m" -ForegroundColor DarkGray }

function Invoke-Step {
  param([string]$Label, [scriptblock]$Body)
  Write-Step $Label
  if ($DryRun) { Write-Dry $Label; return }
  & $Body
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

Write-Info "lsimons-dotfiles Pareto Security tuning"
if ($DryRun) { Write-Dry "dry-run mode -- no changes will be made" }

# ---------------------------------------------------------------------------
# 1. Password after screensaver / on resume
# ---------------------------------------------------------------------------

Invoke-Step "Require password after screensaver (Pareto: password after sleep/screensaver)" {
  # REG_SZ ("1"/"0"), matching what the Screen Saver dialog writes.
  #   ScreenSaverIsSecure = 1  -> prompt for password on resume
  #   ScreenSaveActive    = 1  -> screensaver enabled (so resume-password applies)
  #   ScreenSaveTimeOut   = 300 seconds (well under the 20min Pareto threshold)
  $desktop = 'HKCU:\Control Panel\Desktop'
  $values = @{
    'ScreenSaverIsSecure' = '1'
    'ScreenSaveActive'    = '1'
    'ScreenSaveTimeOut'   = '300'
  }
  foreach ($name in $values.Keys) {
    $val = $values[$name]
    if ($DryRun) {
      Write-Dry "set $desktop\$name = $val (String)"
    } else {
      New-ItemProperty -Path $desktop -Name $name -Value $val -PropertyType String -Force | Out-Null
    }
  }
  if (-not $DryRun) { Write-Ok "screensaver resume-password enabled (sign out/in to apply)" }
}

# ---------------------------------------------------------------------------
# 2. Disable un-passable Pareto checks
# ---------------------------------------------------------------------------

Invoke-Step "Disable un-passable Pareto checks" {
  # Prefer the CLI (writes ~\pareto.toml and validates the UUID). Fall back to
  # the exe shipped in %APPDATA%\ParetoSecurity when it's not on PATH.
  $pareto = Get-Command paretosecurity -ErrorAction SilentlyContinue
  $paretoExe = if ($pareto) {
    $pareto.Source
  } else {
    $candidate = Join-Path $env:APPDATA 'ParetoSecurity\paretosecurity.exe'
    if (Test-Path $candidate) { $candidate } else { $null }
  }

  if (-not $paretoExe) {
    Write-WarnMsg "paretosecurity CLI not found -- install Pareto Security (phase 1) first. Skipping."
    return
  }

  foreach ($uuid in $DisableChecks) {
    if ($DryRun) {
      Write-Dry "$paretoExe config disable $uuid"
    } else {
      & $paretoExe config disable $uuid
      if ($LASTEXITCODE -ne 0) {
        Write-WarnMsg "config disable $uuid exited $LASTEXITCODE"
      } else {
        Write-Ok "disabled check $uuid"
      }
    }
  }
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

Write-Host ""
Write-Ok "Pareto tuning complete."
if (-not $DryRun) {
  Write-Info "Re-check with: paretosecurity status"
}
