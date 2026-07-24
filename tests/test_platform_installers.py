"""Focused tests for macOS installer failure and first-run behavior."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "script"))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


terminal_installer = load_module(
    "dotfiles_terminal_platform", REPO_ROOT / "terminal" / "install.py"
)
mise_installer = load_module(
    "dotfiles_mise_platform", REPO_ROOT / "mise" / "install.py"
)
go_installer = load_module("dotfiles_go_platform", REPO_ROOT / "go" / "install.py")


class TerminalInstallerTests(unittest.TestCase):
    def test_platform_terminal_creates_fresh_preferences_domain(self):
        missing = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="Domain com.apple.Terminal does not exist"
        )
        imported = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with mock.patch.object(
            terminal_installer.subprocess, "run", side_effect=[missing, imported]
        ) as run:
            self.assertTrue(terminal_installer.import_profile({"name": "test"}))
        self.assertEqual(run.call_args_list[1].args[0][0:2], ["defaults", "import"])

    def test_platform_terminal_preserves_other_export_failures(self):
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="permission denied")
        with mock.patch.object(terminal_installer.subprocess, "run", return_value=failed):
            self.assertFalse(terminal_installer.import_profile({"name": "test"}))


class MiseInstallerTests(unittest.TestCase):
    def test_platform_mise_propagates_launchctl_load_failure(self):
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="load failed")
        with tempfile.TemporaryDirectory() as home, mock.patch.object(
            mise_installer.Path, "home", return_value=Path(home)
        ), mock.patch.object(mise_installer, "run_cmd", return_value=failed):
            self.assertFalse(mise_installer.install_launch_agent())

    def test_platform_mise_main_propagates_configuration_failure(self):
        with mock.patch.object(mise_installer, "parse_dry_run"), mock.patch.object(
            mise_installer, "install_mise", return_value=True
        ), mock.patch.object(
            mise_installer, "ensure_minimum_release_age", return_value=False
        ), mock.patch.object(mise_installer, "install_launch_agent") as launch:
            self.assertEqual(mise_installer.main(), 1)
            launch.assert_not_called()

    def test_platform_mise_main_propagates_launch_agent_failure(self):
        with mock.patch.object(mise_installer, "parse_dry_run"), mock.patch.object(
            mise_installer, "install_mise", return_value=True
        ), mock.patch.object(
            mise_installer, "ensure_minimum_release_age", return_value=True
        ), mock.patch.object(
            mise_installer, "install_launch_agent", return_value=False
        ):
            self.assertEqual(mise_installer.main(), 1)


class PrerequisiteGuardTests(unittest.TestCase):
    def test_platform_mise_prerequisite_is_nonfatal_during_dry_run(self):
        with mock.patch.object(go_installer, "parse_dry_run"), mock.patch.object(
            go_installer, "command_exists", return_value=False
        ), mock.patch.object(go_installer, "is_dry_run", return_value=True), mock.patch.object(
            go_installer, "mise_use", return_value=True
        ):
            self.assertEqual(go_installer.main(), 0)


if __name__ == "__main__":
    unittest.main()
