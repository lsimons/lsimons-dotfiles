#!/usr/bin/env python3
"""Open paths in Zed on the machine a Rex terminal or SSH session is used from.

`rex/rc.sh` wraps `zed` with this in every Rex terminal. When the Rex app
that opened the terminal is on another machine, each path is turned into
a `zed://ssh/<this host>/<absolute path>` URL and that app is asked to
open it (its `client.url.open` action), so Zed starts there and reaches
back here over SSH. That needs this host to accept SSH from the other
machine; see the `sshd/` topic.

In an SSH session (SSH_CONNECTION set) outside Rex there is no app to
ask, so the URLs are printed as terminal hyperlinks to click; the
terminal on the other machine opens them there.

Exits with EXIT_LOCAL when there is nothing remote to do: neither a Rex
terminal nor an SSH session, or the Rex app is on this machine. The
wrapper then runs the real `zed`.

Which app: the one that opened this terminal (the block's owner), while
it is still attached to the session. Otherwise the only remote app
attached to the session; with several, it refuses rather than guess.
"Remote" means connected over anything but the server's unix socket.

A Rex app too old to offer `client.url.open` gets the URL printed as a
terminal hyperlink to click instead.
"""

import json
import os
import socket
import subprocess
import sys
from urllib.parse import quote

EXIT_LOCAL = 10
EXIT_ERROR = 1
OPEN_URL_ACTION = "client.url.open"


class RexError(Exception):
    pass


def rex_json(*args):
    """Run a rex command that prints JSON and return the parsed result."""
    try:
        result = subprocess.run(["rex", *args, "--json"], check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RexError("rex is not on PATH") from exc
    if result.returncode != 0:
        raise RexError(f"rex {' '.join(args)} failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RexError(f"rex {' '.join(args)} did not print JSON") from exc


def is_remote(client):
    return client.get("principal", {}).get("transport") != "unix"


def client_label(client):
    return client.get("info", {}).get("label") or client["client_id"]


def pick_client(clients, owner_id, session_id):
    """The remote Rex app to open Zed on, or None to open it locally.

    Raises RexError when several remote apps are attached and none of
    them opened this terminal.
    """
    apps = [
        client
        for client in clients
        if client.get("info", {}).get("kind") == "app"
        and client.get("connection_state") == "connected"
        and session_id in client.get("session_ids", [])
    ]
    for client in apps:
        if client["client_id"] == owner_id:
            return client if is_remote(client) else None
    remote = [client for client in apps if is_remote(client)]
    if len(remote) > 1:
        labels = ", ".join(sorted(client_label(client) for client in remote))
        raise RexError(
            f"this terminal's own Rex app is gone and several remote ones are attached ({labels}); "
            "not guessing which should open Zed"
        )
    return remote[0] if remote else None


def offers_open_url(client_id):
    """Whether that Rex app can be asked to open a URL. Older builds cannot."""
    actions = rex_json("client", "inspect", client_id).get("actions", [])
    return any(action.get("name") == OPEN_URL_ACTION for action in actions)


def hyperlink(url):
    """`url` as an OSC 8 terminal hyperlink, so it can be clicked."""
    return f"\033]8;;{url}\033\\{url}\033]8;;\033\\"


def print_links(message, urls):
    print(message, file=sys.stderr)
    for url in urls:
        print(f"  {hyperlink(url)}", file=sys.stderr)


def ssh_client_address():
    """The address an SSH session comes from, or None outside SSH."""
    fields = os.environ.get("SSH_CONNECTION", "").split()
    return fields[0] if fields else None


def zed_url(host, path, cwd):
    """`zed://ssh/<host>/<absolute path>`, the URL form of `zed ssh://...`."""
    absolute = os.path.normpath(os.path.join(cwd, path))
    return f"zed://ssh/{host}{quote(absolute)}"


def main(argv):
    session_id = os.environ.get("REX_SESSION")
    block_id = os.environ.get("REX_BLOCK")
    ssh_from = ssh_client_address()
    if session_id and block_id:
        try:
            clients = rex_json("client", "ls").get("clients", [])
            owner_id = rex_json("block", "inspect", block_id).get("block", {}).get("owner")
            client = pick_client(clients, owner_id, session_id)
        except RexError as exc:
            print(f"zed: {exc}", file=sys.stderr)
            return EXIT_ERROR
        if client is None:
            return EXIT_LOCAL
        target = client_label(client)
    elif ssh_from:
        client = None
        target = ssh_from
    else:
        return EXIT_LOCAL

    options = [arg for arg in argv if arg.startswith("-")]
    if options:
        print(
            f"zed: {' '.join(options)}: only paths can be sent to Zed on {target}; "
            "use `command zed` for the Zed on this machine",
            file=sys.stderr,
        )
        return EXIT_ERROR

    host = socket.gethostname().split(".")[0]
    cwd = os.getcwd()
    urls = [zed_url(host, path, cwd) for path in argv or ["."]]

    if client is None:
        print_links(f"zed: this is an SSH session from {target}; click to open Zed there:", urls)
        return 0

    try:
        can_open = offers_open_url(client["client_id"])
    except RexError as exc:
        print(f"zed: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if not can_open:
        print_links(
            f"zed: the Rex app on {target} is too old to open links on request "
            f"(no {OPEN_URL_ACTION}); update it, or click:",
            urls,
        )
        return 0

    for url in urls:
        result = subprocess.run(
            ["rex", "-C", client["client_id"], "do", OPEN_URL_ACTION, f"url={url}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"zed: could not open {url} on {client_label(client)}: {result.stderr.strip()}", file=sys.stderr)
            return EXIT_ERROR
        print(f"zed: opened {url} on {client_label(client)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
