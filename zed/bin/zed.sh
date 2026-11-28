#!/usr/bin/env bash
# `zed` on Linux, where the Zed package names its CLI `zeditor`.
# ~/.local/bin/zed links here; see zed/install.py. In a Rex terminal used
# from another machine the `zed` shell function in rex/rc.sh runs first
# and only falls back to this when the Rex app is on this machine.
exec zeditor "$@"
