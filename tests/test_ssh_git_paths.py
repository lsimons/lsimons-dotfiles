import importlib.util
import os
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


ssh_installer = load_module("dotfiles_ssh_installer", REPO_ROOT / "ssh" / "install.py")
git_installer = load_module("dotfiles_git_installer", REPO_ROOT / "git" / "install.py")


class SshGitPathTests(unittest.TestCase):
    def setUp(self):
        helpers.set_dry_run(False)

    def test_op_write_uses_path_and_explicit_account(self):
        with mock.patch.object(ssh_installer.subprocess, "run") as run:
            ssh_installer.op_write_secret("work", "op://vault/key/public", "/key")

        command = run.call_args.args[0]
        self.assertEqual(command[0], "op")
        self.assertEqual(command[1:4], ["read", "--account", "work"])

    def test_askpass_has_explicit_account_and_repairs_mode_when_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            askpass = Path(tmp) / "askpass.sh"
            with mock.patch.object(ssh_installer, "SSH_ASKPASS_AI_PATH", askpass):
                ssh_installer.write_ai_askpass("op://vault/key/password", "work")
                askpass.chmod(0o644)
                ssh_installer.write_ai_askpass("op://vault/key/password", "work")

            self.assertIn(
                "exec op read --account work op://vault/key/password",
                askpass.read_text(),
            )
            self.assertEqual(askpass.stat().st_mode & 0o777, 0o700)

    def test_generated_git_config_uses_effective_xdg_allowed_signers_path(self):
        machine = {
            "git": {
                "user": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "signingkey": None,
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            xdg = Path(tmp) / "custom-config"
            with (
                mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg)}),
                mock.patch.object(
                    git_installer, "get_machine_config", return_value=(machine, "test")
                ),
            ):
                git_installer.generate_config()

            expected = xdg / "git" / "allowed-signers"
            config = (xdg / "git" / "config").read_text()
            ai_config = (xdg / "git" / "config.ai").read_text()
            self.assertIn(f"allowedSignersFile = {expected}", config)
            self.assertIn(f"allowedSignersFile = {expected}", ai_config)


if __name__ == "__main__":
    unittest.main()
