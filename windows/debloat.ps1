#Requires -Version 5.1
<#
.SYNOPSIS
    Remove Windows 11 preinstalled bloat: consumer OneDrive and the personal
    (consumer) Microsoft Teams app.

.DESCRIPTION
    Idempotent: re-running is safe. Each step checks before acting.

    Scope is deliberately narrow -- this only removes the two apps Windows 11
    auto-installs and pins for a personal account:

      * OneDrive              (personal cloud sync client)
      * Teams (personal)      (the consumer "Chat" app, appx MSTeams /
                               MicrosoftTeams)

    It does NOT touch the work/school Teams client (Microsoft.Teams, installed
    machine-wide under Program Files via winget/MSI). That one is left alone so
    a signed-in work account keeps working.

    Run from a NON-admin PowerShell for the per-user removals. Provisioned-
    package removal (stops the apps reinstalling for future users) needs admin;
    it is skipped with a warning when the session is not elevated.

    See ../docs/AGENT_WINDOWS_SETUP.md for rationale.

.PARAMETER DryRun
    Print what would happen without making changes.

.PARAMETER SkipOneDrive
    Leave OneDrive installed.

.PARAMETER SkipTeams
    Leave the personal Teams app installed.

.EXAMPLE
    PS> .\debloat.ps1
    PS> .\debloat.ps1 -DryRun
    PS> .\debloat.ps1 -SkipOneDrive
#>

[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$SkipOneDrive,
  [switch]$SkipTeams
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Info    { param($m) Write-Host "[INFO]    $m" -ForegroundColor Blue }
function Write-Step    { param($m) Write-Host "[STEP]    $m" -ForegroundColor Cyan }
function Write-Ok      { param($m) Write-Host "[OK]      $m" -ForegroundColor Green }
function Write-WarnMsg { param($m) Write-Host "[WARN]    $m" -ForegroundColor Yellow }
function Write-ErrMsg  { param($m) Write-Host "[ERR]     $m" -ForegroundColor Red }
function Write-Dry     { param($m) Write-Host "[DRY-RUN] $m" -ForegroundColor DarkGray }

function Test-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-Step {
  param([string]$Label, [scriptblock]$Body)
  Write-Step $Label
  if ($DryRun) { Write-Dry $Label; return }
  & $Body
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

Write-Info "lsimons-dotfiles Windows debloat"
if ($DryRun) { Write-Dry "dry-run mode -- no changes will be made" }

$isElevated = Test-Admin
if (-not $isElevated) {
  Write-WarnMsg "Not elevated: per-user removals will run, but provisioned-package"
  Write-WarnMsg "removal (stops reinstall for future users) will be skipped."
}

# ---------------------------------------------------------------------------
# Appx removal helper
# ---------------------------------------------------------------------------

function Remove-AppxByName {
  # $Patterns: wildcard package-name patterns for the CURRENT-USER appx.
  # Removes the installed package for this user and, when elevated, the
  # provisioned copy so it doesn't return for freshly created accounts.
  param([string[]]$Patterns, [string]$Label)

  $installed = @()
  foreach ($p in $Patterns) {
    $installed += Get-AppxPackage -Name $p -ErrorAction SilentlyContinue
  }

  if (-not $installed) {
    Write-Ok "$Label not installed for this user"
  } else {
    foreach ($pkg in $installed) {
      if ($DryRun) {
        Write-Dry "Remove-AppxPackage $($pkg.PackageFullName)"
      } else {
        Remove-AppxPackage -Package $pkg.PackageFullName -ErrorAction Stop
        Write-Ok "removed $($pkg.Name)"
      }
    }
  }

  # Provisioned package (machine-wide staging for new users) -- needs admin.
  if (-not $isElevated) {
    Write-WarnMsg "${Label}: skipping provisioned-package removal (not elevated)"
    return
  }

  $prov = @()
  foreach ($p in $Patterns) {
    $prov += Get-AppxProvisionedPackage -Online |
             Where-Object { $_.DisplayName -like $p }
  }
  if (-not $prov) {
    Write-Ok "$Label not provisioned"
    return
  }
  foreach ($pp in $prov) {
    if ($DryRun) {
      Write-Dry "Remove-AppxProvisionedPackage $($pp.PackageName)"
    } else {
      Remove-AppxProvisionedPackage -Online -PackageName $pp.PackageName -ErrorAction Stop | Out-Null
      Write-Ok "deprovisioned $($pp.DisplayName)"
    }
  }
}

# ---------------------------------------------------------------------------
# Teams (personal / consumer)
# ---------------------------------------------------------------------------

if (-not $SkipTeams) {
  Invoke-Step "Remove personal Teams (consumer app; work Teams is left alone)" {
    # MSTeams          = the new unified preinstalled consumer app (Win11 22H2+)
    # MicrosoftTeams   = the older "Chat" consumer app
    # NOT Microsoft.Teams (work/school MSI under Program Files) -- untouched.
    Remove-AppxByName -Patterns @('MSTeams', 'MicrosoftTeams') -Label 'Teams (personal)'
  }

  Invoke-Step "Disable the taskbar Chat/Teams button" {
    # TaskbarMn = 0 unpins the auto-pinned Chat button.
    $advanced = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
    if ($DryRun) {
      Write-Dry "set $advanced\TaskbarMn = 0"
    } else {
      if (-not (Test-Path $advanced)) { New-Item -Path $advanced -Force | Out-Null }
      New-ItemProperty -Path $advanced -Name 'TaskbarMn' -Value 0 -PropertyType DWord -Force | Out-Null
      Write-Ok "Chat button disabled (restart Explorer or sign out to see it go)"
    }
  }
}

# ---------------------------------------------------------------------------
# OneDrive
# ---------------------------------------------------------------------------

if (-not $SkipOneDrive) {
  Invoke-Step "Check for OneDrive Known Folder Move before uninstalling" {
    # If OneDrive redirected Desktop/Documents/Pictures into its folder, the
    # files live under %USERPROFILE%\OneDrive, and online-only files are not
    # present locally. Uninstalling then makes them look like they vanished.
    # Warn loudly rather than silently proceeding.
    $oneDriveRoot = Join-Path $env:USERPROFILE 'OneDrive'
    $shellFolders = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
    $redirected = @()
    foreach ($name in 'Desktop', 'Personal', 'My Pictures') {
      $val = (Get-ItemProperty -Path $shellFolders -Name $name -ErrorAction SilentlyContinue).$name
      if ($val -and $val -like '*OneDrive*') { $redirected += $name }
    }
    if ($redirected.Count -gt 0) {
      Write-WarnMsg "Known Folder Move is active for: $($redirected -join ', ')"
      Write-WarnMsg "Your files live under: $oneDriveRoot"
      Write-WarnMsg "Before uninstalling, ensure those files are downloaded locally"
      Write-WarnMsg "(OneDrive settings -> free up space is the opposite of what you want),"
      Write-WarnMsg "or move the contents of $oneDriveRoot back under $env:USERPROFILE."
      if (-not $DryRun) {
        Write-WarnMsg "Continuing in 10s -- Ctrl+C to abort and sort out KFM first."
        Start-Sleep -Seconds 10
      }
    } else {
      Write-Ok "no Known Folder Move detected -- safe to uninstall"
    }
  }

  Invoke-Step "Uninstall OneDrive" {
    # OneDriveSetup.exe /uninstall is the supported uninstaller. It ships in
    # System32 (64-bit) and SysWOW64 (32-bit); use whichever exists.
    $setup = @(
      Join-Path $env:SystemRoot 'System32\OneDriveSetup.exe'
      Join-Path $env:SystemRoot 'SysWOW64\OneDriveSetup.exe'
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $setup) {
      # Fall back to winget (per-user MSIX builds register there).
      if (Get-Command winget -ErrorAction SilentlyContinue) {
        if ($DryRun) {
          Write-Dry "winget uninstall Microsoft.OneDrive"
        } else {
          # Stop the running client first so the uninstaller isn't blocked.
          Get-Process OneDrive -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
          winget uninstall --id Microsoft.OneDrive --silent --accept-source-agreements 2>&1 | Out-Null
          Write-Ok "OneDrive uninstalled via winget (or was already absent)"
        }
      } else {
        Write-WarnMsg "OneDriveSetup.exe not found and winget unavailable -- OneDrive may already be gone"
      }
      return
    }

    if ($DryRun) {
      Write-Dry "$setup /uninstall"
      return
    }
    Get-Process OneDrive -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath $setup -ArgumentList '/uninstall' -Wait
    Write-Ok "OneDrive uninstalled"
  }

  Invoke-Step "Remove OneDrive from startup (Run key)" {
    $runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    $existing = Get-ItemProperty -Path $runKey -Name 'OneDrive' -ErrorAction SilentlyContinue
    if (-not $existing) {
      Write-Ok "no OneDrive Run entry"
    } elseif ($DryRun) {
      Write-Dry "remove $runKey\OneDrive"
    } else {
      Remove-ItemProperty -Path $runKey -Name 'OneDrive' -ErrorAction SilentlyContinue
      Write-Ok "removed OneDrive Run entry"
    }
  }
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

Write-Host ""
Write-Ok "Debloat complete."
Write-Info ""
Write-Info "Notes:"
Write-Info "  - Windows feature updates may re-pin Teams / reinstall OneDrive."
Write-Info "    Re-run this script after major updates."
Write-Info "  - Work/school Teams (Microsoft.Teams) was NOT removed."
Write-Info "  - Sign out / restart Explorer to clear the taskbar Chat button."
