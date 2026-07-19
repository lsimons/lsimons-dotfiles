import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "script"))

import helpers  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load_module("dotfiles_main_installer", REPO_ROOT / "script" / "install.py")
onepassword = load_module(
    "dotfiles_onepassword_installer", REPO_ROOT / "1password" / "install.py"
)


class InstallerCoreTests(unittest.TestCase):
    def setUp(self):
        helpers.set_dry_run(False)

    def test_homebrew_python_comes_from_formula_prefix(self):
        result = mock.Mock(stdout="/opt/homebrew/opt/python@3\n")
        with mock.patch.object(installer, "run_command", return_value=result) as run:
            python = installer.get_homebrew_python()

        self.assertEqual(python, "/opt/homebrew/opt/python@3/bin/python3")
        run.assert_called_once_with(
            ["brew", "--prefix", "python@3"], capture_output=True
        )

    def test_unknown_topic_dependency_fails(self):
        topics = {"git": Path("git/install.py")}
        self.assertIsNone(installer.topological_sort(topics, {"git": ["missing"]}))

    def test_link_file_resolves_relative_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "repo" / "config"
            source.parent.mkdir()
            source.write_text("content")
            destination = root / "home" / ".config" / "tool" / "config"

            old_cwd = Path.cwd()
            try:
                os.chdir(root)
                helpers.link_file(Path("repo/config"), destination)
            finally:
                os.chdir(old_cwd)

            self.assertEqual(destination.readlink(), source.resolve())
            self.assertEqual(destination.resolve(), source.resolve())

    def test_backups_preserve_home_relative_paths_and_do_not_collide(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            first = home / ".config" / "one" / "config"
            second = home / ".config" / "two" / "config"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text("one")
            second.write_text("two")

            with (
                mock.patch.object(helpers, "HOME", home),
                mock.patch.object(helpers, "NOW", "timestamp"),
            ):
                helpers.backup_file(first)
                helpers.backup_file(second)

            backup = home / ".dotfiles-backup" / "timestamp" / ".config"
            self.assertEqual((backup / "one" / "config").read_text(), "one")
            self.assertEqual((backup / "two" / "config").read_text(), "two")

    def test_directory_link_does_not_delete_existing_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            source = Path(tmp) / "source"
            destination = home / ".config" / "tool"
            old_backup = destination.with_suffix(".backup")
            source.mkdir()
            destination.mkdir(parents=True)
            (destination / "current").write_text("current")
            old_backup.mkdir()
            (old_backup / "keep").write_text("keep")

            with (
                mock.patch.object(helpers, "HOME", home),
                mock.patch.object(helpers, "NOW", "timestamp"),
            ):
                helpers.link_directory(source, destination)

            self.assertEqual((old_backup / "keep").read_text(), "keep")
            archived = home / ".dotfiles-backup" / "timestamp" / ".config/tool"
            self.assertEqual((archived / "current").read_text(), "current")
            self.assertEqual(destination.resolve(), source.resolve())

    def test_onepassword_uses_canonical_path_and_migrates_lowercase_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            xdg = Path(tmp)
            legacy = xdg / "1password"
            legacy.mkdir()
            (legacy / "existing").write_text("content")
            canonical = xdg / "1Password"

            with (
                mock.patch.object(onepassword, "XDG_CONFIG_HOME", xdg),
                mock.patch.object(onepassword, "OP_CONFIG_DIR", canonical),
            ):
                onepassword.migrate_legacy_config_dir()

            self.assertNotIn("1password", {entry.name for entry in xdg.iterdir()})
            self.assertEqual((canonical / "existing").read_text(), "content")

    def test_onepassword_agent_entries_include_the_account(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "1Password" / "ssh"
            agent_toml = config_dir / "agent.toml"
            machine = {
                "ssh": {
                    "keys": [
                        {
                            "name": "work-key",
                            "op_vault": "Employee",
                            "op_account": "work",
                            "auth": True,
                        }
                    ]
                }
            }
            with (
                mock.patch.object(onepassword, "OP_SSH_CONFIG_DIR", config_dir),
                mock.patch.object(onepassword, "SSH_AGENT_TOML", agent_toml),
                mock.patch.object(
                    onepassword, "get_machine_config", return_value=(machine, "test")
                ),
            ):
                onepassword.install_1password_ssh_agent_config()

            self.assertIn('account = "work"', agent_toml.read_text())

    def test_commented_toml_table_header_is_updated_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.toml"
            config.write_text('[settings] # managed settings\nminimum_release_age = "1d"\n')

            helpers.set_toml_value(
                config, "settings", "minimum_release_age", "7d"
            )

            content = config.read_text()
            self.assertEqual(content.count("[settings]"), 1)
            self.assertIn('minimum_release_age = "7d"', content)

    def test_symlink_mappings_expand_all_xdg_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic = Path(tmp)
            (topic / "symlinks.txt").write_text(
                "data.symlink -> $XDG_DATA_HOME/tool/data\n"
                "cache.symlink -> $XDG_CACHE_HOME/tool/cache\n"
                "state.symlink -> $XDG_STATE_HOME/tool/state\n"
            )
            with (
                mock.patch.object(helpers, "XDG_DATA_HOME_STR", "/xdg/data"),
                mock.patch.object(helpers, "XDG_CACHE_HOME_STR", "/xdg/cache"),
                mock.patch.object(helpers, "XDG_STATE_HOME_STR", "/xdg/state"),
            ):
                mappings = helpers.load_symlink_mappings(topic)

            self.assertEqual(mappings["data.symlink"], Path("/xdg/data/tool/data"))
            self.assertEqual(
                mappings["cache.symlink"], Path("/xdg/cache/tool/cache")
            )
            self.assertEqual(
                mappings["state.symlink"], Path("/xdg/state/tool/state")
            )


if __name__ == "__main__":
    unittest.main()
