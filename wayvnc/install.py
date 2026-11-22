#!/usr/bin/env python3
"""Installation script for the wayvnc remote-desktop host.

Opt-in per machine through `remoteAccess.wayvnc` in
`machines/<hostname>.json`; every other machine skips this topic. On an
enabled machine it:

* installs wayvnc, a VNC server for wlroots-style Wayland compositors
  (Hyprland implements the screencopy and virtual-input protocols it
  needs);
* writes and enables a systemd user unit that starts wayvnc with the
  desktop session, bound to this machine's Tailscale IPv4 address and
  nothing else. The address is looked up at start time, so the unit
  survives the node being re-enrolled;
* opens 5900/tcp in ufw for the tailnet's CGNAT range only;
* requires a login as the desktop user, checked by PAM against the
  system password, over RSA-AES (TigerVNC, RealVNC). macOS Screen
  Sharing does not work: it only asks for a password, never a user;
* locks VNC logins for 10 minutes after 3 consecutive failures, using
  pam_faillock with its own tally so VNC guessing never locks the local
  login or lock screen. `/etc/pam.d/wayvnc` belongs to the wayvnc
  package and is overwritten on every upgrade (it is not a pacman
  backup file), so a pacman hook restores our copy after each upgrade.

wayvnc is chosen over Sunshine deliberately: it copies frames through
shared memory and encodes on the CPU, so it never touches the GPU buffer
path that exhausted memory on snow. The tailnet is the first line of
access control, which is why the bind address matters; the PAM login is
the second.

Inspect or clear the VNC lockout with
`faillock --dir ~/.local/state/wayvnc/faillock --user $USER [--reset]`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import (
    IS_ARCH,
    XDG_CONFIG_HOME,
    XDG_STATE_HOME_STR,
    dry,
    ensure_package,
    error,
    get_remote_access_config,
    info,
    is_dry_run,
    make_dir,
    parse_dry_run,
    run_cmd,
    success,
    sudo_write_file,
    systemctl_enable,
    ufw_allow,
    write_file,
)

PORT = 5900
# Tailscale hands every node an address from this range.
TAILNET_CIDR = "100.64.0.0/10"

UNIT_NAME = "wayvnc.service"
UNIT_PATH = XDG_CONFIG_HOME / "systemd" / "user" / UNIT_NAME
UNIT = f"""\
# Managed by lsimons-dotfiles (wayvnc/install.py). Do not edit by hand.
[Unit]
Description=wayvnc remote desktop, bound to this machine's Tailscale address
After=graphical-session.target
PartOf=graphical-session.target

[Service]
# The tailnet address is looked up on every start; tailscaled may not be
# up yet when the session starts, which Restart= covers.
ExecStart=/bin/sh -c 'exec wayvnc "$(tailscale ip -4)" {PORT}'
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=graphical-session.target
"""


CONFIG_DIR = XDG_CONFIG_HOME / "wayvnc"
CONFIG_PATH = CONFIG_DIR / "config"
RSA_KEY_PATH = CONFIG_DIR / "rsa_key.pem"
CONFIG = f"""\
# Managed by lsimons-dotfiles (wayvnc/install.py). Do not edit by hand.
# Address and port come from the command line in {UNIT_NAME}.
enable_auth=true
enable_pam=true
rsa_private_key_file={RSA_KEY_PATH}
"""

# Lockout policy for VNC logins. The tally lives in the user's state
# directory, not /run/faillock, so VNC failures never lock the local
# login. wayvnc runs as the user, so the user must be able to write it.
FAILLOCK_DENY = 3
FAILLOCK_UNLOCK_SECONDS = 600
FAILLOCK_DIR = Path(XDG_STATE_HOME_STR) / "wayvnc" / "faillock"

PAM_PATH = Path("/etc/pam.d/wayvnc")
_FAILLOCK_ARGS = f"deny={FAILLOCK_DENY} unlock_time={FAILLOCK_UNLOCK_SECONDS} dir={FAILLOCK_DIR}"
PAM = f"""\
#%PAM-1.0
# Managed by lsimons-dotfiles (wayvnc/install.py). Do not edit by hand.
# A pacman hook restores this after wayvnc upgrades overwrite it.
auth     required                 pam_faillock.so preauth silent {_FAILLOCK_ARGS}
auth     [success=1 default=bad]  pam_unix.so nodelay
auth     [default=die]            pam_faillock.so authfail {_FAILLOCK_ARGS}
auth     required                 pam_faillock.so authsucc {_FAILLOCK_ARGS}
account  required                 pam_unix.so
"""
# The copy the pacman hook restores from. Outside /etc/pam.d so it is
# not itself a PAM service.
PAM_MASTER_PATH = Path("/etc/lsimons-dotfiles/wayvnc.pam")

PACMAN_HOOK_PATH = Path("/etc/pacman.d/hooks/90-lsimons-dotfiles-wayvnc-pam.hook")
PACMAN_HOOK = f"""\
# Managed by lsimons-dotfiles (wayvnc/install.py). Do not edit by hand.
# The wayvnc package ships {PAM_PATH} without marking it a backup file,
# so every upgrade overwrites our lockout policy. Put it back.
[Trigger]
Operation = Install
Operation = Upgrade
Type = Package
Target = wayvnc

[Action]
Description = Restoring the lsimons-dotfiles wayvnc PAM config...
When = PostTransaction
Exec = /usr/bin/install -m 0644 {PAM_MASTER_PATH} {PAM_PATH}
"""


def install_wayvnc():
    return ensure_package("wayvnc", pacman="wayvnc", command="wayvnc")


def install_unit():
    """Write the user unit and make systemd see it. Returns True on success."""
    if UNIT_PATH.exists() and UNIT_PATH.read_text() == UNIT:
        success(f"{UNIT_PATH} already up to date")
        return True
    write_file(UNIT_PATH, UNIT)
    if is_dry_run():
        dry("would run: systemctl --user daemon-reload")
        return True
    result = run_cmd(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
    if result.returncode != 0:
        error(f"systemctl --user daemon-reload failed: {(result.stderr or '').strip()}")
        return False
    success(f"Wrote {UNIT_PATH}")
    return True


def install_pam():
    """Write the PAM policy, its master copy and the pacman hook.

    The master copy and the hook go first, so the live file is never in
    place without the means to restore it. Returns True on success.
    """
    make_dir(FAILLOCK_DIR, mode=0o700)
    for path, content in (
        (PAM_MASTER_PATH, PAM),
        (PACMAN_HOOK_PATH, PACMAN_HOOK),
        (PAM_PATH, PAM),
    ):
        sudo_write_file(path, content)
        if not is_dry_run() and _read(path) != content:
            error(f"{path} does not have the expected content")
            return False
    return True


def _read(path):
    try:
        return path.read_text()
    except OSError:
        return None


def install_config():
    """Generate the RSA key if missing and write the wayvnc config.

    Returns (ok, changed); `changed` means a running wayvnc must restart
    to pick it up.
    """
    changed = False
    if RSA_KEY_PATH.exists():
        success(f"{RSA_KEY_PATH} already exists")
    elif is_dry_run():
        dry(f"would generate {RSA_KEY_PATH}")
        changed = True
    else:
        make_dir(CONFIG_DIR, mode=0o700)
        result = run_cmd(
            ["ssh-keygen", "-q", "-m", "pem", "-t", "rsa", "-b", "3072",
             "-N", "", "-C", "wayvnc", "-f", str(RSA_KEY_PATH)],
            check=False, capture_output=True,
        )
        if result.returncode != 0:
            error(f"ssh-keygen failed: {(result.stderr or '').strip()}")
            return False, changed
        RSA_KEY_PATH.chmod(0o600)
        success(f"Generated {RSA_KEY_PATH}")
        changed = True

    if _read(CONFIG_PATH) == CONFIG:
        success(f"{CONFIG_PATH} already up to date")
    else:
        write_file(CONFIG_PATH, CONFIG, mode=0o600)
        if not is_dry_run():
            success(f"Wrote {CONFIG_PATH}")
        changed = True
    return True, changed


def restart_unit():
    """Restart wayvnc if it is running. Ends any open VNC session."""
    if is_dry_run():
        dry(f"would run: systemctl --user try-restart {UNIT_NAME}")
        return True
    result = run_cmd(["systemctl", "--user", "try-restart", UNIT_NAME], check=False, capture_output=True)
    if result.returncode != 0:
        error(f"systemctl --user try-restart {UNIT_NAME} failed: {(result.stderr or '').strip()}")
        return False
    success(f"{UNIT_NAME} restarted to apply the new config")
    return True


def main():
    parse_dry_run()

    remote = get_remote_access_config()
    if not remote.get("wayvnc"):
        info("remoteAccess.wayvnc is not enabled for this machine; skipping wayvnc")
        return 0

    if not IS_ARCH:
        error("wayvnc hosting is only set up for Arch here")
        return 1

    info("Installing the wayvnc remote-desktop host...")
    if not install_wayvnc():
        return 1
    if not install_pam():
        return 1
    config_ok, config_changed = install_config()
    if not config_ok:
        return 1
    if not install_unit():
        return 1
    if not systemctl_enable(UNIT_NAME, user=True):
        return 1
    if config_changed and not restart_unit():
        return 1
    if not ufw_allow(PORT, "tcp", "wayvnc", from_cidr=TAILNET_CIDR):
        return 1

    info(f"Connect a VNC viewer to this machine's tailnet name on port {PORT}; log in as your user")
    return 0


if __name__ == '__main__':
    sys.exit(main())
