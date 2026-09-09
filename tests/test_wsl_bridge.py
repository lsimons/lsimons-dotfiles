"""Tests for the WSL 1Password integration: the agent bridge, the op.exe
wrapper and the ssh-keygen signing helper."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "script"))

import helpers


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


onepassword = load_module("dotfiles_wsl_onepassword", REPO_ROOT / "1password" / "install.py")
ssh_installer = load_module("dotfiles_wsl_ssh", REPO_ROOT / "ssh" / "install.py")


class WindowsExecutableLookupTests(unittest.TestCase):
    def test_prefers_the_interop_path(self):
        with mock.patch.object(onepassword.shutil, "which", return_value="/mnt/c/x/op.exe"):
            self.assertEqual(onepassword.find_windows_exe("op.exe"), Path("/mnt/c/x/op.exe"))

    def test_falls_back_to_any_users_scoop_shims(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            onepassword.shutil, "which", return_value=None
        ), mock.patch.object(onepassword, "WINDOWS_USERS_DIR", Path(tmp)):
            self.assertIsNone(onepassword.find_windows_exe("npiperelay.exe"))
            shim = Path(tmp) / "leo" / "scoop" / "shims" / "npiperelay.exe"
            shim.parent.mkdir(parents=True)
            shim.write_bytes(b"MZ")
            self.assertEqual(onepassword.find_windows_exe("npiperelay.exe"), shim)


class AgentBridgeTests(unittest.TestCase):
    def setUp(self):
        helpers.set_dry_run(False)

    def test_bridge_script_relays_the_agent_pipe_into_the_linux_socket(self):
        script = onepassword.render_bridge_script(Path("/mnt/c/scoop/npiperelay.exe"))
        self.assertTrue(script.startswith("#!/bin/sh\n"))
        self.assertIn(f'socket="{helpers.OP_LINUX_AGENT_SOCKET}"', script)
        self.assertIn("exec socat", script)
        self.assertIn("/mnt/c/scoop/npiperelay.exe -ei -s //./pipe/openssh-ssh-agent", script)

    def test_unit_runs_the_script_and_starts_with_the_session(self):
        unit = onepassword.render_bridge_unit()
        self.assertIn(f"ExecStart={onepassword.BRIDGE_SCRIPT}", unit)
        self.assertIn("WantedBy=default.target", unit)

    def test_missing_npiperelay_warns_instead_of_failing(self):
        with mock.patch.object(onepassword, "ensure_package", return_value=True), mock.patch.object(
            onepassword, "find_windows_exe", return_value=None
        ), mock.patch.object(onepassword, "run_cmd") as run:
            self.assertTrue(onepassword.install_wsl_agent_bridge())
        run.assert_not_called()

    def test_bridge_is_installed_enabled_and_restarted_on_change(self):
        ok = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            onepassword, "ensure_package", return_value=True
        ), mock.patch.object(
            onepassword, "find_windows_exe", return_value=Path("/mnt/c/scoop/npiperelay.exe")
        ), mock.patch.object(
            onepassword, "BRIDGE_SCRIPT", Path(tmp) / "bridge.sh"
        ), mock.patch.object(
            onepassword, "BRIDGE_UNIT", Path(tmp) / "1password-agent-bridge.service"
        ), mock.patch.object(onepassword, "run_cmd", return_value=ok) as run:
            self.assertTrue(onepassword.install_wsl_agent_bridge())
            first = [call.args[0] for call in run.call_args_list]
            run.reset_mock()
            self.assertTrue(onepassword.install_wsl_agent_bridge())
            second = [call.args[0] for call in run.call_args_list]
            self.assertEqual((Path(tmp) / "bridge.sh").stat().st_mode & 0o777, 0o755)

        self.assertEqual(first[0], ["systemctl", "--user", "daemon-reload"])
        self.assertEqual(
            first[1], ["systemctl", "--user", "enable", "--now", "1password-agent-bridge.service"]
        )
        self.assertEqual(first[2][:3], ["systemctl", "--user", "restart"])
        # Unchanged files: no restart, so an idle bridge is not bounced.
        self.assertEqual(len(second), 2)

    def test_systemctl_failure_fails_the_topic(self):
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="no bus")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            onepassword, "ensure_package", return_value=True
        ), mock.patch.object(
            onepassword, "find_windows_exe", return_value=Path("/mnt/c/scoop/npiperelay.exe")
        ), mock.patch.object(
            onepassword, "BRIDGE_SCRIPT", Path(tmp) / "bridge.sh"
        ), mock.patch.object(
            onepassword, "BRIDGE_UNIT", Path(tmp) / "unit.service"
        ), mock.patch.object(onepassword, "run_cmd", return_value=failed):
            self.assertFalse(onepassword.install_wsl_agent_bridge())


class OpWrapperTests(unittest.TestCase):
    def setUp(self):
        helpers.set_dry_run(False)

    def test_wrapper_execs_the_windows_cli(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            onepassword, "find_windows_exe", return_value=Path("/mnt/c/Program Files/op.exe")
        ), mock.patch.object(onepassword, "OP_WRAPPER", Path(tmp) / "bin" / "op"):
            self.assertTrue(onepassword.install_op_wrapper())
            wrapper = Path(tmp) / "bin" / "op"
            self.assertEqual(wrapper.stat().st_mode & 0o777, 0o755)
            self.assertIn('exec "/mnt/c/Program Files/op.exe" "$@"', wrapper.read_text())

    def test_without_op_exe_the_caller_installs_the_linux_cli(self):
        with mock.patch.object(onepassword, "find_windows_exe", return_value=None), mock.patch.object(
            onepassword, "write_file"
        ) as write:
            self.assertFalse(onepassword.install_op_wrapper())
        write.assert_not_called()

    def test_wsl_main_skips_the_linux_cli_when_op_exe_serves(self):
        with mock.patch.object(
            onepassword, "get_machine_config", return_value=({"ssh": {"keys": []}}, "poppy")
        ), mock.patch.object(onepassword, "IS_WSL", True), mock.patch.object(
            onepassword, "migrate_legacy_config_dir"
        ), mock.patch.object(
            onepassword, "install_wsl_agent_bridge", return_value=True
        ), mock.patch.object(
            onepassword, "install_op_wrapper", return_value=True
        ), mock.patch.object(onepassword, "ensure_package") as ensure:
            self.assertEqual(onepassword.main(), 0)
        ensure.assert_not_called()


class SigningHelperTests(unittest.TestCase):
    def setUp(self):
        helpers.set_dry_run(False)

    def test_helper_signs_with_ssh_keygen_through_the_bridged_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            helper = Path(tmp) / "sign.sh"
            with mock.patch.object(ssh_installer, "SSH_SIGN_BRIDGE_PATH", helper):
                ssh_installer.write_bridge_sign_helper()
                helper.chmod(0o644)
                ssh_installer.write_bridge_sign_helper()
            content = helper.read_text()
            self.assertEqual(helper.stat().st_mode & 0o777, 0o700)
        self.assertIn(f'export SSH_AUTH_SOCK="{helpers.OP_LINUX_AGENT_SOCKET}"', content)
        self.assertIn('exec ssh-keygen "$@"', content)


if __name__ == "__main__":
    unittest.main()
