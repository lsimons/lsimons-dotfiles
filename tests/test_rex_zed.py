"""Tests for rex/zed_remote.py, the `zed` wrapper for Rex terminals.

The costly mistakes: opening Zed on a machine nobody is sitting at,
sending a relative path that means something else on the other side, and
swallowing the local `zed` when nothing remote is involved.
"""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


zed_remote = load_module("dotfiles_rex_zed_remote", REPO_ROOT / "rex" / "zed_remote.py")

SESSION = "session:1"


def client(client_id, transport, kind="app", sessions=(SESSION,), state="connected"):
    return {
        "client_id": client_id,
        "info": {"kind": kind, "label": client_id},
        "principal": {"transport": transport},
        "connection_state": state,
        "session_ids": list(sessions),
    }


LOCAL = client("local", "unix")
REMOTE = client("remote", "tailscale")
OTHER = client("other", "tailscale")


class PickClientTests(unittest.TestCase):
    def test_remote_owner_wins_over_an_attached_local_app(self):
        self.assertIs(zed_remote.pick_client([LOCAL, REMOTE], "remote", SESSION), REMOTE)

    def test_local_owner_means_local_zed_even_with_a_remote_app_attached(self):
        self.assertIsNone(zed_remote.pick_client([LOCAL, REMOTE], "local", SESSION))

    def test_falls_back_to_the_only_remote_app_when_the_owner_is_gone(self):
        self.assertIs(zed_remote.pick_client([LOCAL, REMOTE], "gone", SESSION), REMOTE)

    def test_refuses_to_guess_between_remote_apps(self):
        with self.assertRaises(zed_remote.RexError):
            zed_remote.pick_client([REMOTE, OTHER], "gone", SESSION)

    def test_ignores_cli_clients_other_sessions_and_disconnected_apps(self):
        clients = [
            client("cli", "tailscale", kind="cli"),
            client("elsewhere", "tailscale", sessions=("session:2",)),
            client("asleep", "tailscale", state="disconnected"),
        ]
        self.assertIsNone(zed_remote.pick_client(clients, "gone", SESSION))


class ZedUrlTests(unittest.TestCase):
    def test_relative_paths_become_absolute_on_this_host(self):
        self.assertEqual(zed_remote.zed_url("host", ".", "/home/me/repo"), "zed://ssh/host/home/me/repo")
        self.assertEqual(
            zed_remote.zed_url("host", "../x/a b.txt", "/home/me/repo"),
            "zed://ssh/host/home/me/x/a%20b.txt",
        )

    def test_absolute_paths_are_kept(self):
        self.assertEqual(zed_remote.zed_url("host", "/etc/hosts", "/home/me"), "zed://ssh/host/etc/hosts")


class MainTests(unittest.TestCase):
    def run_main(self, argv, clients, owner="remote", env=None):
        env = {"REX_SESSION": SESSION, "REX_BLOCK": "block:1"} if env is None else env

        def rex_json(*args):
            return {"clients": clients} if args[0] == "client" else {"block": {"owner": owner}}

        ok = mock.Mock(returncode=0, stderr="")
        with mock.patch.dict(zed_remote.os.environ, env, clear=True), mock.patch.object(
            zed_remote, "rex_json", side_effect=rex_json
        ), mock.patch.object(zed_remote.subprocess, "run", return_value=ok) as run, mock.patch.object(
            zed_remote.socket, "gethostname", return_value="host.example.internal"
        ), mock.patch.object(zed_remote.os, "getcwd", return_value="/work"):
            return zed_remote.main(argv), run

    def test_outside_rex_it_defers_to_the_local_zed(self):
        code, run = self.run_main(["a"], [REMOTE], env={})
        self.assertEqual(code, zed_remote.EXIT_LOCAL)
        run.assert_not_called()

    def test_local_app_defers_to_the_local_zed_options_and_all(self):
        code, run = self.run_main(["--wait", "a"], [LOCAL], owner="local")
        self.assertEqual(code, zed_remote.EXIT_LOCAL)
        run.assert_not_called()

    def test_opens_each_path_on_the_remote_app(self):
        code, run = self.run_main(["a", "/b"], [LOCAL, REMOTE])
        self.assertEqual(code, 0)
        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                ["rex", "-C", "remote", "do", "client.url.open", "url=zed://ssh/host/work/a"],
                ["rex", "-C", "remote", "do", "client.url.open", "url=zed://ssh/host/b"],
            ],
        )

    def test_no_path_opens_the_current_directory(self):
        _, run = self.run_main([], [REMOTE])
        self.assertEqual(run.call_args.args[0][-1], "url=zed://ssh/host/work")

    def test_options_are_refused_for_a_remote_app(self):
        code, run = self.run_main(["--wait", "a"], [REMOTE])
        self.assertEqual(code, zed_remote.EXIT_ERROR)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
