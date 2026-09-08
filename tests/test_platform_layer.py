"""Tests for the macOS/Linux platform abstraction.

These cover the pieces that decide *what* runs where — package-manager
dispatch, per-topic platform gating, and per-platform symlink
destinations — rather than any one topic's installer.
"""

import importlib.util
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


installer = load_module("dotfiles_platform_installer", REPO_ROOT / "script" / "install.py")


class DistroDetectionTests(unittest.TestCase):
    def _ids(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "os-release"
            path.write_text(text)
            return helpers._linux_distro_ids(path)

    def test_id_like_marks_arch_derivatives_as_arch(self):
        """Omarchy runs Arch Linux ARM, whose ID is archarm, not arch."""
        ids = self._ids('NAME="Arch Linux ARM"\nID=archarm\nID_LIKE=arch\n')
        self.assertIn("arch", ids)
        self.assertIn("archarm", ids)

    def test_quoted_and_multi_valued_id_like_is_split(self):
        ids = self._ids('ID=omarchy\nID_LIKE="arch archarm"\n')
        self.assertEqual(ids, {"omarchy", "arch", "archarm"})

    def test_missing_os_release_is_not_an_error(self):
        self.assertEqual(
            helpers._linux_distro_ids(Path("/nonexistent/os-release")), set()
        )


class EnsurePackageTests(unittest.TestCase):
    def setUp(self):
        helpers.set_dry_run(False)

    def test_command_probe_short_circuits_before_any_package_manager(self):
        with mock.patch.object(
            helpers, "command_exists", return_value=True
        ), mock.patch.object(helpers, "brew_install") as brew, mock.patch.object(
            helpers, "pacman_install"
        ) as pacman:
            self.assertTrue(helpers.ensure_package("jq", brew="jq", pacman="jq", command="jq"))
        brew.assert_not_called()
        pacman.assert_not_called()

    def test_macos_uses_brew_and_linux_uses_pacman(self):
        for is_macos, installed_with in ((True, "brew"), (False, "pacman")):
            with self.subTest(macos=is_macos), mock.patch.object(
                helpers, "IS_MACOS", is_macos
            ), mock.patch.object(helpers, "IS_LINUX", not is_macos), mock.patch.object(
                helpers, "brew_is_installed", return_value=False
            ), mock.patch.object(
                helpers, "pacman_is_installed", return_value=False
            ), mock.patch.object(
                helpers, "pacman_repo_has", return_value=True
            ), mock.patch.object(
                helpers, "brew_install", return_value=True
            ) as brew, mock.patch.object(
                helpers, "pacman_install", return_value=True
            ) as pacman:
                self.assertTrue(
                    helpers.ensure_package("gh", brew="gh", pacman="github-cli")
                )
                if installed_with == "brew":
                    brew.assert_called_once_with("gh", cask=False)
                    pacman.assert_not_called()
                else:
                    pacman.assert_called_once_with("github-cli")
                    brew.assert_not_called()

    def test_aur_fallback_when_the_package_is_in_no_repo(self):
        with mock.patch.object(helpers, "IS_MACOS", False), mock.patch.object(
            helpers, "IS_LINUX", True
        ), mock.patch.object(
            helpers, "pacman_is_installed", return_value=False
        ), mock.patch.object(
            helpers, "pacman_repo_has", return_value=False
        ), mock.patch.object(
            helpers, "pacman_install"
        ) as pacman, mock.patch.object(
            helpers, "aur_install", return_value=True
        ) as aur:
            self.assertTrue(helpers.ensure_package("topgrade", aur="topgrade"))
        pacman.assert_not_called()
        aur.assert_called_once_with("topgrade")

    def test_missing_package_name_for_this_platform_fails_loudly(self):
        """A topic with no Arch package must not quietly report success."""
        with mock.patch.object(helpers, "IS_MACOS", False), mock.patch.object(
            helpers, "IS_LINUX", True
        ), mock.patch.object(helpers, "command_exists", return_value=False):
            self.assertFalse(helpers.ensure_package("dockutil", brew="dockutil"))

    def test_optional_downgrades_a_missing_package_to_a_warning(self):
        with mock.patch.object(helpers, "IS_MACOS", False), mock.patch.object(
            helpers, "IS_LINUX", True
        ), mock.patch.object(helpers, "command_exists", return_value=False):
            self.assertTrue(
                helpers.ensure_package("dockutil", brew="dockutil", optional=True)
            )

    def test_optional_also_absorbs_an_install_failure(self):
        with mock.patch.object(helpers, "IS_MACOS", False), mock.patch.object(
            helpers, "IS_LINUX", True
        ), mock.patch.object(
            helpers, "command_exists", return_value=False
        ), mock.patch.object(
            helpers, "pacman_is_installed", return_value=False
        ), mock.patch.object(
            helpers, "pacman_repo_has", return_value=False
        ), mock.patch.object(helpers, "aur_install", return_value=False):
            self.assertTrue(
                helpers.ensure_package("ghostty", pacman="ghostty", optional=True)
            )

    def test_dry_run_installs_nothing_and_reports_success(self):
        helpers.set_dry_run(True)
        self.addCleanup(helpers.set_dry_run, False)
        with mock.patch.object(helpers.subprocess, "run") as run:
            self.assertTrue(
                helpers.ensure_package("jq", brew="jq", pacman="jq", command="jq")
            )
        run.assert_not_called()


class BrewWithoutHomebrewTests(unittest.TestCase):
    """The brew_* helpers are called on Linux by legacy-migration paths."""

    def setUp(self):
        helpers.set_dry_run(False)

    def test_probes_answer_no_rather_than_raising(self):
        with mock.patch.object(helpers.shutil, "which", return_value=None):
            self.assertFalse(helpers.brew_is_installed("gemini-cli"))
            # "Nothing to uninstall" is success, not failure.
            self.assertTrue(helpers.brew_uninstall("gemini-cli"))
            self.assertFalse(helpers.brew_install("gemini-cli"))


class TopicPlatformTests(unittest.TestCase):
    def test_topic_without_platforms_txt_runs_everywhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(installer.get_topic_platforms(Path(tmp)))
            self.assertTrue(installer.topic_supported(Path(tmp)))

    def test_platforms_txt_gates_the_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic = Path(tmp)
            (topic / "platforms.txt").write_text("# only on a Mac\nmacos\n")
            self.assertEqual(installer.get_topic_platforms(topic), {"macos"})
            with mock.patch.object(installer, "PLATFORM", "macos"):
                self.assertTrue(installer.topic_supported(topic))
            with mock.patch.object(installer, "PLATFORM", "linux"):
                self.assertFalse(installer.topic_supported(topic))

    def test_repo_macos_only_topics_are_declared(self):
        """These topics drive Dock/Terminal.app/swiftDialog or replace a
        tool Linux already has, so they must never run on Linux."""
        for name in ("dock", "terminal", "swiftdialog", "timeout"):
            with self.subTest(topic=name):
                self.assertEqual(
                    installer.get_topic_platforms(REPO_ROOT / name), {"macos"}
                )


class PlatformSymlinkMappingTests(unittest.TestCase):
    def test_platform_prefix_selects_one_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic = Path(tmp)
            (topic / "symlinks.txt").write_text(
                "# comment\n"
                "macos: config.symlink -> $HOME/Library/App/config\n"
                "linux: config.symlink -> $XDG_CONFIG_HOME/app/config\n"
                "theme.symlink -> $XDG_CONFIG_HOME/app/theme\n"
            )
            mac = helpers.load_symlink_mappings(topic, "macos")
            linux = helpers.load_symlink_mappings(topic, "linux")

        self.assertTrue(str(mac["config.symlink"]).endswith("/Library/App/config"))
        self.assertTrue(str(linux["config.symlink"]).endswith("/app/config"))
        # An unprefixed line applies on both.
        self.assertEqual(mac["theme.symlink"], linux["theme.symlink"])

    def test_ghostty_config_lands_in_the_native_location_on_each_platform(self):
        mac = helpers.load_symlink_mappings(REPO_ROOT / "ghostty", "macos")
        linux = helpers.load_symlink_mappings(REPO_ROOT / "ghostty", "linux")
        self.assertIn(
            "Library/Application Support/com.mitchellh.ghostty",
            str(mac["config.symlink"]),
        )
        self.assertNotIn("Library", str(linux["config.symlink"]))
        self.assertTrue(str(linux["config.symlink"]).endswith("/ghostty/config"))


class OnePasswordIntegrationPathTests(unittest.TestCase):
    """1Password installs its agent socket and signing shim elsewhere on Linux.

    Both are module-level constants derived from helpers.IS_MACOS, so the
    modules are re-imported with that flag forced either way.
    """

    def _load(self, name, relative_path, is_macos):
        with mock.patch.object(helpers, "IS_MACOS", is_macos):
            return load_module(f"{name}_{is_macos}", REPO_ROOT / relative_path)

    def test_ssh_agent_socket_is_platform_native(self):
        mac = self._load("ssh_installer", "ssh/install.py", True)
        linux = self._load("ssh_installer", "ssh/install.py", False)
        self.assertIn(
            "Library/Group Containers/2BUA8C4S2C.com.1password",
            str(mac.OP_AGENT_SOCKET),
        )
        self.assertTrue(str(linux.OP_AGENT_SOCKET).endswith("/.1password/agent.sock"))

    def test_op_ssh_sign_is_platform_native(self):
        mac = self._load("git_installer", "git/install.py", True)
        linux = self._load("git_installer", "git/install.py", False)
        self.assertEqual(
            mac.GPG_SSH_PROGRAM_DEFAULT,
            "/Applications/1Password.app/Contents/MacOS/op-ssh-sign",
        )
        self.assertEqual(linux.GPG_SSH_PROGRAM_DEFAULT, "/opt/1Password/op-ssh-sign")


class GitEditorFallbackTests(unittest.TestCase):
    """core.editor must name an editor that is actually installed.

    Zed has no aarch64 Linux build, so hard-coding `zed --wait` there
    leaves git launching a binary that is not there.
    """

    def setUp(self):
        self.git_installer = load_module(
            "dotfiles_git_editor", REPO_ROOT / "git" / "install.py"
        )

    def test_prefers_zed_when_present(self):
        with mock.patch.object(
            self.git_installer, "command_exists", lambda cmd: cmd == "zed"
        ):
            self.assertEqual(self.git_installer.resolve_editor(), "zed --wait")

    def test_uses_the_linux_zed_binary_name(self):
        with mock.patch.object(
            self.git_installer, "command_exists", lambda cmd: cmd == "zeditor"
        ):
            self.assertEqual(self.git_installer.resolve_editor(), "zeditor --wait")

    def test_falls_back_to_a_terminal_editor(self):
        with mock.patch.object(
            self.git_installer, "command_exists", lambda cmd: cmd == "nvim"
        ):
            self.assertEqual(self.git_installer.resolve_editor(), "nvim")

    def test_falls_back_to_vim_when_nothing_is_installed(self):
        with mock.patch.object(
            self.git_installer, "command_exists", return_value=False
        ):
            self.assertEqual(self.git_installer.resolve_editor(), "vim")


if __name__ == "__main__":
    unittest.main()
