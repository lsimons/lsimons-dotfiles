"""Tests for the private overlay: config merging and machine validation."""

import importlib.util
import json
import sys
import tempfile
import tomllib
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


check = load_module("dotfiles_check_private_overlay", REPO_ROOT / "script" / "check.py")
helpers = load_module("dotfiles_helpers_private_overlay", REPO_ROOT / "script" / "helpers.py")
codex = load_module("dotfiles_codex_private_overlay", REPO_ROOT / "codex" / "install.py")


class LinkOrMergeJsonTests(unittest.TestCase):
    def setUp(self):
        helpers.set_dry_run(False)
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "settings.json.base"
        self.src.write_text('// comment\n{"theme": "light", "models": {"a": 1}}\n')
        self.dst = self.tmp / "out" / "settings.json"

    def test_without_overlay_links_the_public_file(self):
        helpers.link_or_merge_json(self.src, self.dst, None)
        self.assertTrue(self.dst.is_symlink())
        self.assertEqual(self.dst.resolve(), self.src.resolve())

    def test_overlay_replaces_symlink_with_merged_file(self):
        overlay = self.tmp / "overlay.json"
        overlay.write_text('{"models": {"b": 2}}')
        helpers.link_or_merge_json(self.src, self.dst, None)

        helpers.link_or_merge_json(self.src, self.dst, overlay)

        self.assertFalse(self.dst.is_symlink())
        self.assertEqual(
            json.loads(self.dst.read_text()), {"theme": "light", "models": {"a": 1, "b": 2}}
        )

    def test_changed_merged_file_is_backed_up_before_rewrite(self):
        overlay = self.tmp / "overlay.json"
        overlay.write_text('{"models": {"b": 2}}')
        self.dst.parent.mkdir(parents=True)
        self.dst.write_text('{"edited": "in the app"}\n')

        with mock.patch.object(helpers, "backup_file") as backup:
            helpers.link_or_merge_json(self.src, self.dst, overlay)

        backup.assert_called_once_with(self.dst)


class CodexTomlOverlayTests(unittest.TestCase):
    def test_overlay_keys_go_before_base_and_tables_after(self):
        base = 'personality = "pragmatic"\n\n[tui]\nstatus_line = []\n'
        keys, tables = codex.split_toml_overlay(
            '# comment\nmodel = "m"\n\n[model_providers.p]\nname = "P"\n'
        )
        merged = tomllib.loads(f"{keys}\n{base}\n{tables}")
        self.assertEqual(merged["model"], "m")
        self.assertEqual(merged["personality"], "pragmatic")
        self.assertEqual(merged["model_providers"], {"p": {"name": "P"}})

    def test_overlay_without_tables_is_all_keys(self):
        self.assertEqual(codex.split_toml_overlay('model = "m"\n'), ('model = "m"\n', ""))


class PrivateMachineValidationTests(unittest.TestCase):
    def test_private_machine_file_is_validated_merged_over_public_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "public"
            private_root = Path(temp_dir) / "private"
            (repo_root / "machines").mkdir(parents=True)
            (private_root / "machines").mkdir(parents=True)
            (repo_root / "machines" / "default.json").write_text(
                json.dumps({"git": {"user": {"name": "N", "email": "e@example.com"}}})
            )
            (private_root / "machines" / "work-laptop.json").write_text(
                json.dumps({"git": {"user": {"signingkey": "missing-key"}}})
            )

            with (
                mock.patch.object(check, "REPO_ROOT", repo_root),
                mock.patch.object(check, "PRIVATE_ROOT", private_root),
            ):
                errors = check.check_machine_configs()

        self.assertTrue(
            any(
                "private:machines/work-laptop.json" in error
                and "unknown SSH key 'missing-key'" in error
                for error in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
