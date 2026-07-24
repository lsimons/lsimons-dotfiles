import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "agents/sync-repo-config.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_repo_config_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MiseTaskTomlParsingTests(unittest.TestCase):
    def test_parse_tasks_supports_valid_toml_forms(self):
        module = load_sync_module()
        content = '''
[tasks]
inline = "echo inline"
"quoted:name" = { run = "echo quoted" }

[tasks.multiline]
description = "A table declared across lines"
run = "echo multiline"
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            mise_toml = Path(tmpdir) / ".mise.toml"
            mise_toml.write_text(content)
            self.assertEqual(
                module.parse_tasks(mise_toml),
                ["inline", "quoted:name", "multiline"],
            )

    def test_parse_tasks_ignores_non_task_tables(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            mise_toml = Path(tmpdir) / ".mise.toml"
            mise_toml.write_text('[tools]\npython = "3.14"\n')
            self.assertEqual(module.parse_tasks(mise_toml), [])


if __name__ == "__main__":
    unittest.main()
