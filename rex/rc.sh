# In a Rex terminal or an SSH session, `zed PATH` opens Zed on the machine
# the shell is being used from, over SSH back to this one. zed_remote.py
# asks the Rex app to open it, or over plain SSH prints a link to click,
# and exits 10 when there is nothing remote to do (the Rex app is on this
# machine), in which case the real zed runs. Elsewhere `zed` is left
# alone.
if [ -n "${REX_SESSION:-}" ] || [ -n "${SSH_CONNECTION:-}" ]; then
  zed() {
    local rc
    python3 "$HOME/.dotfiles/rex/zed_remote.py" "$@"
    rc=$?
    if [ "$rc" -eq 10 ]; then
      command zed "$@"
      return
    fi
    return "$rc"
  }
fi
