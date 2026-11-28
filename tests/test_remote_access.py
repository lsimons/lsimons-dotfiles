"""Tests for the opt-in remote-access topics (sshd, wayvnc, rex) and the
`remoteAccess` machine-config block that gates them.

The costly mistakes here are all lock-outs or surprise exposure: turning
off password login before a key is authorized, running the host topics
on a machine that never asked for them, a typo in the machine config
silently disabling the gate, wayvnc listening anywhere but the tailnet,
and wayvnc's login lockout going missing. So that is what these cover.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "script"))

import check
import helpers


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sshd = load_module("dotfiles_sshd", REPO_ROOT / "sshd" / "install.py")
wayvnc = load_module("dotfiles_wayvnc", REPO_ROOT / "wayvnc" / "install.py")
rex = load_module("dotfiles_rex", REPO_ROOT / "rex" / "install.py")

KEY_A = "ssh-ed25519 AAAAexampleA a@example"
KEY_B = "ssh-ed25519 AAAAexampleB b@example"


class RemoteAccessSchemaTests(unittest.TestCase):
    def test_accepts_the_snow_shaped_block(self):
        errors = check.validate_machine_data(
            {
                "remoteAccess": {
                    "allowFrom": "192.168.2.0/24",
                    "rex": True,
                    "sshd": True,
                    "wayvnc": True,
                }
            },
            "machine.json",
        )
        self.assertEqual(errors, [])

    def test_rejects_stringly_typed_flags_and_unknown_keys(self):
        errors = check.validate_machine_data(
            {"remoteAccess": {"sshd": "yes", "sunshine": True}}, "machine.json"
        )
        self.assertIn("machine.json:$.remoteAccess.sshd: must be a bool", errors)
        self.assertIn("machine.json:$.remoteAccess.sunshine: unknown key", errors)


class GateTests(unittest.TestCase):
    def test_sshd_skips_when_not_enabled(self):
        with mock.patch.object(sshd, "parse_dry_run"), mock.patch.object(
            sshd, "get_remote_access_config", return_value={}
        ), mock.patch.object(sshd, "install_server") as install:
            self.assertEqual(sshd.main(), 0)
        install.assert_not_called()

    def test_wayvnc_skips_when_not_enabled(self):
        with mock.patch.object(wayvnc, "parse_dry_run"), mock.patch.object(
            wayvnc, "get_remote_access_config", return_value={"sshd": True}
        ), mock.patch.object(wayvnc, "install_wayvnc") as install:
            self.assertEqual(wayvnc.main(), 0)
        install.assert_not_called()


class AuthorizedKeysTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        ssh_dir = Path(self.tmp.name) / ".ssh"
        self.path = ssh_dir / "authorized_keys"
        patcher = mock.patch.multiple(
            sshd, SSH_CONFIG_DIR=ssh_dir, AUTHORIZED_KEYS=self.path
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        helpers.set_dry_run(False)

    def test_only_auth_keys_are_selected(self):
        with mock.patch.object(
            sshd,
            "get_machine_ssh_config",
            return_value={
                "keys": [
                    {"public_key": KEY_A, "auth": True},
                    {"public_key": KEY_B, "auth": False},
                ]
            },
        ):
            self.assertEqual(sshd.authorized_public_keys(), [KEY_A])

    def test_appends_without_duplicating_or_dropping_manual_keys(self):
        self.path.parent.mkdir()
        self.path.write_text(f"# by hand\n{KEY_B}\n")
        self.assertEqual(sshd.install_authorized_keys([KEY_A, KEY_B]), 2)
        self.assertEqual(sshd.install_authorized_keys([KEY_A, KEY_B]), 2)
        self.assertEqual(
            self.path.read_text().splitlines(), ["# by hand", KEY_B, KEY_A]
        )
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_dry_run_writes_nothing(self):
        helpers.set_dry_run(True)
        self.addCleanup(helpers.set_dry_run, False)
        self.assertEqual(sshd.install_authorized_keys([KEY_A]), 1)
        self.assertFalse(self.path.exists())


class HardeningTests(unittest.TestCase):
    def setUp(self):
        # The Linux path: a snippet that exists, and a daemon to reload.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        snippet = Path(tmp.name) / "10-lsimons-dotfiles.conf"
        snippet.write_text(sshd.HARDENING)
        patcher = mock.patch.multiple(sshd, IS_MACOS=False, HARDENING_PATH=snippet)
        patcher.start()
        self.addCleanup(patcher.stop)
        helpers.set_dry_run(False)

    def test_password_login_stays_on_without_a_key(self):
        with mock.patch.object(sshd, "sudo_write_file") as write:
            self.assertTrue(sshd.harden(0))
        write.assert_not_called()

    def test_reloads_sshd_only_when_the_snippet_changed(self):
        ok = mock.Mock(returncode=0, stderr="")
        with mock.patch.object(sshd, "sudo_write_file", return_value=False), mock.patch.object(
            sshd, "run_cmd", return_value=ok
        ) as run:
            self.assertTrue(sshd.harden(1))
        run.assert_not_called()
        with mock.patch.object(sshd, "sudo_write_file", return_value=True), mock.patch.object(
            sshd, "run_cmd", return_value=ok
        ) as run:
            self.assertTrue(sshd.harden(1))
        self.assertEqual(run.call_args.args[0][:3], ["sudo", "systemctl", "reload"])


class MacosTests(unittest.TestCase):
    """On macOS the topic authorizes keys and stops there: turning the
    server on, the system sshd_config and the firewall are the user's."""

    def run_main(self, remote_login):
        with mock.patch.object(sshd, "parse_dry_run"), mock.patch.object(
            sshd, "get_remote_access_config", return_value={"sshd": True}
        ), mock.patch.object(sshd, "IS_MACOS", True), mock.patch.object(
            sshd, "authorized_public_keys", return_value=[KEY_A]
        ), mock.patch.object(
            sshd, "install_authorized_keys", return_value=1
        ) as keys, mock.patch.object(
            sshd, "run_cmd", return_value=mock.Mock(returncode=0 if remote_login else 113)
        ) as run, mock.patch.object(sshd, "install_server") as server, mock.patch.object(
            sshd, "systemctl_enable"
        ) as enable, mock.patch.object(sshd, "harden", return_value=True) as harden, mock.patch.object(
            sshd, "ufw_allow"
        ) as allow:
            self.assertEqual(sshd.main(), 0)
        keys.assert_called_once_with([KEY_A])
        harden.assert_called_once_with(1)
        for untouched in (server, enable, allow):
            untouched.assert_not_called()
        return run

    def test_hardening_writes_the_snippet_and_reloads_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            snippet = Path(tmp) / "10-lsimons-dotfiles.conf"

            def write(path, content):
                snippet.write_text(content)
                return True

            with mock.patch.object(sshd, "IS_MACOS", True), mock.patch.object(
                sshd, "HARDENING_PATH", snippet
            ), mock.patch.object(sshd, "sudo_write_file", side_effect=write), mock.patch.object(
                sshd, "run_cmd"
            ) as run:
                self.assertTrue(sshd.harden(1))
            self.assertIn("PasswordAuthentication no", snippet.read_text())
        run.assert_not_called()

    def test_hardening_fails_when_the_snippet_could_not_be_written(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            sshd, "IS_MACOS", True
        ), mock.patch.object(sshd, "HARDENING_PATH", Path(tmp) / "missing.conf"), mock.patch.object(
            sshd, "sudo_write_file", return_value=False
        ):
            self.assertFalse(sshd.harden(1))

    def test_only_authorizes_keys_and_reads_remote_login(self):
        run = self.run_main(remote_login=True)
        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [["launchctl", "print", "system/com.openssh.sshd"]],
        )

    def test_remote_login_off_is_reported_not_changed(self):
        run = self.run_main(remote_login=False)
        self.assertEqual(len(run.call_args_list), 1)
        self.assertEqual(run.call_args.args[0][:2], ["launchctl", "print"])


class WayvncTests(unittest.TestCase):
    def test_unit_binds_to_the_tailscale_address_only(self):
        exec_start = next(
            line for line in wayvnc.UNIT.splitlines() if line.startswith("ExecStart=")
        )
        self.assertIn('"$(tailscale ip -4)"', exec_start)
        self.assertIn(str(wayvnc.PORT), exec_start)
        self.assertIn("WantedBy=graphical-session.target", wayvnc.UNIT)

    def test_firewall_rule_is_scoped_to_the_tailnet(self):
        with mock.patch.object(wayvnc, "parse_dry_run"), mock.patch.object(
            wayvnc, "get_remote_access_config", return_value={"wayvnc": True}
        ), mock.patch.object(wayvnc, "IS_ARCH", True), mock.patch.object(
            wayvnc, "install_wayvnc", return_value=True
        ), mock.patch.object(wayvnc, "install_pam", return_value=True), mock.patch.object(
            wayvnc, "install_config", return_value=(True, False)
        ), mock.patch.object(wayvnc, "install_unit", return_value=True), mock.patch.object(
            wayvnc, "systemctl_enable", return_value=True
        ), mock.patch.object(wayvnc, "ufw_allow", return_value=True) as allow:
            self.assertEqual(wayvnc.main(), 0)
        allow.assert_called_once()
        self.assertEqual(allow.call_args.kwargs["from_cidr"], "100.64.0.0/10")
        self.assertEqual(allow.call_args.args[:2], (5900, "tcp"))

    def test_unit_is_rewritten_only_when_it_differs(self):
        helpers.set_dry_run(False)
        with tempfile.TemporaryDirectory() as tmp:
            unit_path = Path(tmp) / "wayvnc.service"
            ok = mock.Mock(returncode=0, stderr="")
            with mock.patch.object(wayvnc, "UNIT_PATH", unit_path), mock.patch.object(
                wayvnc, "run_cmd", return_value=ok
            ) as run:
                self.assertTrue(wayvnc.install_unit())
                self.assertTrue(wayvnc.install_unit())
            self.assertEqual(unit_path.read_text(), wayvnc.UNIT)
        run.assert_called_once()

    def test_config_requires_a_pam_login(self):
        lines = wayvnc.CONFIG.splitlines()
        self.assertIn("enable_auth=true", lines)
        self.assertIn("enable_pam=true", lines)
        self.assertIn(f"rsa_private_key_file={wayvnc.RSA_KEY_PATH}", lines)
        self.assertNotIn("relax_encryption=true", lines)

    def test_pam_locks_out_after_three_failures_in_a_private_tally(self):
        faillock = [line for line in wayvnc.PAM.splitlines() if "pam_faillock.so" in line]
        self.assertEqual(
            [line.split()[3] for line in faillock], ["preauth", "authfail", "authsucc"]
        )
        for line in faillock:
            self.assertIn("deny=3", line)
            self.assertIn("unlock_time=600", line)
            self.assertIn(f"dir={wayvnc.FAILLOCK_DIR}", line)
        self.assertNotIn("/run/faillock", wayvnc.PAM)

    def test_pacman_hook_restores_the_pam_file_after_upgrades(self):
        hook = wayvnc.PACMAN_HOOK
        self.assertIn("Operation = Upgrade", hook)
        self.assertIn("Target = wayvnc", hook)
        self.assertIn(f"{wayvnc.PAM_MASTER_PATH} {wayvnc.PAM_PATH}", hook)
        self.assertFalse(str(wayvnc.PAM_MASTER_PATH).startswith("/etc/pam.d/"))

    def test_config_change_restarts_wayvnc_and_rerun_does_not(self):
        helpers.set_dry_run(False)
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "wayvnc"
            key = config_dir / "rsa_key.pem"

            def keygen(cmd, **kwargs):
                key.write_text("key")
                return mock.Mock(returncode=0, stderr="")

            with mock.patch.object(wayvnc, "CONFIG_DIR", config_dir), mock.patch.object(
                wayvnc, "CONFIG_PATH", config_dir / "config"
            ), mock.patch.object(wayvnc, "RSA_KEY_PATH", key), mock.patch.object(
                wayvnc, "run_cmd", side_effect=keygen
            ) as run:
                self.assertEqual(wayvnc.install_config(), (True, True))
                self.assertEqual(wayvnc.install_config(), (True, False))
            run.assert_called_once()
            self.assertEqual((config_dir / "config").read_text(), wayvnc.CONFIG)
            self.assertEqual(key.stat().st_mode & 0o777, 0o600)


class RexTests(unittest.TestCase):
    """Rex on the tailnet is remote shell access: it must follow the
    machine's opt-in, and the installer must never restart the server
    (that ends every session, maybe the one running the install)."""

    def setUp(self):
        helpers.set_dry_run(False)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.drop_in = Path(self.tmp.name) / "rex.service.d" / "tailscale.conf"
        self.ok = mock.Mock(returncode=0, stderr="", stdout="")

    def run_main(self, remote):
        with mock.patch.object(rex, "parse_dry_run"), mock.patch.object(
            rex, "is_omarchy", return_value=True
        ), mock.patch.object(rex, "trust_signing_key", return_value=True), mock.patch.object(
            rex, "configure_repo", return_value=True
        ), mock.patch.object(rex, "ensure_package", return_value=True), mock.patch.object(
            rex, "enable_linger", return_value=True
        ), mock.patch.object(rex, "systemctl_enable", return_value=True) as enable, mock.patch.object(
            rex, "get_remote_access_config", return_value=remote
        ), mock.patch.object(rex, "get_short_hostname", return_value="host"), mock.patch.object(
            rex, "DROP_IN_PATH", self.drop_in
        ), mock.patch.object(rex, "run_cmd", return_value=self.ok) as run:
            self.assertEqual(rex.main(), 0)
        return enable, run

    def test_drop_in_serves_on_the_tailnet_when_enabled(self):
        self.run_main({"rex": True})
        exec_starts = [
            line for line in self.drop_in.read_text().splitlines() if line.startswith("ExecStart=")
        ]
        self.assertEqual(exec_starts[0], "ExecStart=")
        self.assertIn("--tailscale --tailscale-hostname host-rex", exec_starts[1])
        self.assertNotIn("--listen", exec_starts[1])

    def test_drop_in_is_removed_when_not_enabled(self):
        self.drop_in.parent.mkdir(parents=True)
        self.drop_in.write_text("stale")
        self.run_main({"sshd": True})
        self.assertFalse(self.drop_in.exists())

    def test_enables_both_units_and_never_restarts(self):
        enable, run = self.run_main({"rex": True})
        self.assertEqual([c.args[0] for c in enable.call_args_list], ["rex.socket", "rex.service"])
        for call in run.call_args_list:
            self.assertNotIn("restart", call.args[0])

    def test_skips_off_omarchy(self):
        with mock.patch.object(rex, "parse_dry_run"), mock.patch.object(
            rex, "is_omarchy", return_value=False
        ), mock.patch.object(rex, "trust_signing_key") as trust:
            self.assertEqual(rex.main(), 0)
        trust.assert_not_called()

    def test_refuses_a_key_with_the_wrong_fingerprint(self):
        with mock.patch.object(rex, "key_is_trusted", return_value=False), mock.patch.object(
            rex, "run_cmd", return_value=self.ok
        ) as run, mock.patch.object(rex, "fingerprints_of", return_value=["0" * 40]):
            self.assertFalse(rex.trust_signing_key())
        self.assertFalse(any(c.args[0][:2] == ["sudo", "pacman-key"] for c in run.call_args_list))


if __name__ == "__main__":
    unittest.main()
