#!/usr/bin/env python3
"""Installation script for Rex (https://superlogical.com).

On Omarchy this sets up a personal Rex server:

* the `[rex]` pacman repository, trusting only Superlogical's signing
  key, pinned by fingerprint below;
* the `rex` package;
* `rex.socket` and `rex.service` as systemd user units, the same state
  `rex server install --user` leaves behind;
* lingering for the account, so the server and every session in it
  survive logging out and start at boot.

Reaching the server over Tailscale is remote shell access, so like the
other hosts it is opt-in per machine, through `remoteAccess.rex` in
`machines/<hostname>.json`. On an enabled machine a drop-in for
rex.service adds `--tailscale --tailscale-hostname <host>-rex`; on any
other machine a stale drop-in is removed.

A package upgrade or drop-in change never restarts rex.service here: a
restart ends every Rex session, possibly the one running this installer.
The installer says so and leaves the restart to the user.

macOS: the Rex GUI. Not set up yet.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
from helpers import (
    XDG_CONFIG_HOME,
    dry,
    ensure_package,
    error,
    get_remote_access_config,
    get_short_hostname,
    info,
    is_dry_run,
    is_omarchy,
    parse_dry_run,
    run_cmd,
    success,
    sudo_write_file,
    systemctl_enable,
    warn,
    write_file,
)

# Superlogical Package Signing <hello@superlogical.com>. The key is
# downloaded from KEY_URL but only trusted when it has this fingerprint.
KEY_FINGERPRINT = "E28636AC71905C6DDE40C1EDFAA6B80F641307A7"
KEY_URL = "https://pkgs.superlogical.com/rex/keys/rex.asc"

PACMAN_CONF = Path("/etc/pacman.conf")
REPO_CONF_PATH = Path("/etc/pacman.d/rex.conf")
REPO_INCLUDE = f"Include = {REPO_CONF_PATH}"
REPO_DB_PATH = Path("/var/lib/pacman/sync/rex.db")
REPO_CONF = (
    "# Managed by lsimons-dotfiles (rex/install.py). Do not edit by hand.\n"
    "[rex]\n"
    "SigLevel = Required DatabaseRequired\n"
    "Server = https://pkgs.superlogical.com/rex/arch/snapshot/$arch\n"
)

UNITS = ("rex.socket", "rex.service")

DROP_IN_PATH = XDG_CONFIG_HOME / "systemd" / "user" / "rex.service.d" / "tailscale.conf"


def drop_in_content(hostname):
    # Clearing ExecStart and setting it again is how rex.service itself
    # says to change the server's flags. Keep it in step with the
    # packaged ExecStart, minus --listen (the socket stays the default).
    return (
        "# Managed by lsimons-dotfiles (rex/install.py). Do not edit by hand.\n"
        "# Serve Rex on the tailnet as well as the local socket.\n"
        "[Service]\n"
        "ExecStart=\n"
        "ExecStart=/usr/bin/rex server run --log-format text"
        f" --tailscale --tailscale-hostname {hostname}-rex\n"
    )


def key_is_trusted():
    result = run_cmd(["pacman-key", "--list-keys", KEY_FINGERPRINT], check=False, capture_output=True)
    return result.returncode == 0


def fingerprints_of(key_path):
    """Primary-key fingerprints in an OpenPGP key file, without importing it."""
    result = run_cmd(
        ["gpg", "--with-colons", "--show-keys", str(key_path)], check=False, capture_output=True
    )
    if result.returncode != 0:
        return []
    fingerprints = []
    after_pub = False
    for line in (result.stdout or "").splitlines():
        fields = line.split(":")
        if fields[0] == "pub":
            after_pub = True
        elif fields[0] == "fpr" and after_pub:
            fingerprints.append(fields[9])
            after_pub = False
    return fingerprints


def trust_signing_key():
    if is_dry_run():
        dry(f"would add and locally sign the Rex package key {KEY_FINGERPRINT} if missing")
        return True
    if key_is_trusted():
        success("Rex package signing key already trusted")
        return True
    with tempfile.TemporaryDirectory() as tmp:
        key_path = Path(tmp) / "rex.asc"
        result = run_cmd(["curl", "-fsSL", "-o", str(key_path), KEY_URL], check=False, capture_output=True)
        if result.returncode != 0:
            error(f"Could not download {KEY_URL}: {(result.stderr or '').strip()}")
            return False
        found = fingerprints_of(key_path)
        if found != [KEY_FINGERPRINT]:
            error(f"{KEY_URL} holds {found or 'no keys'}, expected only {KEY_FINGERPRINT}; not trusting it")
            return False
        for cmd in (
            ["sudo", "pacman-key", "--add", str(key_path)],
            ["sudo", "pacman-key", "--lsign-key", KEY_FINGERPRINT],
        ):
            result = run_cmd(cmd, check=False, capture_output=True)
            if result.returncode != 0:
                error(f"{' '.join(cmd)} failed: {(result.stderr or '').strip()}")
                return False
    success(f"Trusted Rex package signing key {KEY_FINGERPRINT}")
    return True


def configure_repo():
    sudo_write_file(REPO_CONF_PATH, REPO_CONF)

    if REPO_INCLUDE in PACMAN_CONF.read_text().splitlines():
        success(f"{PACMAN_CONF} already includes {REPO_CONF_PATH}")
    elif is_dry_run():
        dry(f"would append '{REPO_INCLUDE}' to {PACMAN_CONF}")
    else:
        result = subprocess.run(
            ["sudo", "tee", "-a", str(PACMAN_CONF)],
            input=f"\n{REPO_INCLUDE}\n", text=True,
            stdout=subprocess.DEVNULL, check=False,
        )
        if result.returncode != 0:
            error(f"Could not add '{REPO_INCLUDE}' to {PACMAN_CONF}")
            return False
        success(f"Added '{REPO_INCLUDE}' to {PACMAN_CONF}")

    # A new repo has no sync database until the next `pacman -Sy`. Sync
    # only this repo, through a config that lists nothing else: a bare
    # `pacman -Sy` would refresh every repo without upgrading, the
    # partial-upgrade state Arch warns against. Later updates arrive with
    # the regular `pacman -Syu`.
    if REPO_DB_PATH.exists():
        return True
    if is_dry_run():
        dry(f"would sync the [rex] database into {REPO_DB_PATH}")
        return True
    with tempfile.NamedTemporaryFile("w", suffix=".conf") as conf:
        conf.write("[options]\nArchitecture = auto\n\n" + REPO_CONF)
        conf.flush()
        result = run_cmd(["sudo", "pacman", "--config", conf.name, "-Sy"], check=False, capture_output=True)
    if result.returncode != 0:
        error(f"Syncing the [rex] database failed: {(result.stderr or '').strip()}")
        return False
    success("Synced the [rex] package database")
    return True


def configure_tailscale_drop_in(enabled):
    """Write or remove the drop-in. Returns (ok, changed)."""
    if enabled:
        content = drop_in_content(get_short_hostname())
        if DROP_IN_PATH.exists() and DROP_IN_PATH.read_text() == content:
            success(f"{DROP_IN_PATH} already up to date")
            return True, False
        write_file(DROP_IN_PATH, content)
    else:
        if not DROP_IN_PATH.exists():
            return True, False
        if is_dry_run():
            dry(f"would remove {DROP_IN_PATH}")
            return True, True
        DROP_IN_PATH.unlink()
        info(f"Removed {DROP_IN_PATH}: remoteAccess.rex is not enabled for this machine")

    if is_dry_run():
        dry("would run: systemctl --user daemon-reload")
        return True, True
    result = run_cmd(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
    if result.returncode != 0:
        error(f"systemctl --user daemon-reload failed: {(result.stderr or '').strip()}")
        return False, True
    return True, True


def enable_linger():
    if is_dry_run():
        dry("would run: loginctl enable-linger (if not already on)")
        return True
    user = Path.home().name
    result = run_cmd(["loginctl", "show-user", user, "--property=Linger", "--value"], check=False, capture_output=True)
    if (result.stdout or "").strip() == "yes":
        success("Lingering already on")
        return True
    result = run_cmd(["sudo", "loginctl", "enable-linger", user], check=False, capture_output=True)
    if result.returncode != 0:
        error(f"loginctl enable-linger failed: {(result.stderr or '').strip()}")
        return False
    success("Lingering turned on")
    return True


def main():
    parse_dry_run()

    if not is_omarchy():
        info("Rex is only set up on Omarchy so far; skipping")
        return 0

    info("Installing the Rex server...")
    if not trust_signing_key():
        return 1
    if not configure_repo():
        return 1
    if not ensure_package("Rex", pacman="rex", command="rex"):
        return 1

    tailscale = bool(get_remote_access_config().get("rex"))
    ok, changed = configure_tailscale_drop_in(tailscale)
    if not ok:
        return 1

    for unit in UNITS:
        if not systemctl_enable(unit, user=True):
            return 1
    if not enable_linger():
        return 1

    if changed:
        warn(
            "rex.service settings changed. Restart it to apply, which ends every Rex session:\n"
            "  systemctl --user restart rex.service"
        )
    if tailscale:
        info(f"Rex is reachable on the tailnet as {get_short_hostname()}-rex")
    return 0


if __name__ == "__main__":
    sys.exit(main())
