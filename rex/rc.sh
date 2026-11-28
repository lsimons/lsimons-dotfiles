# In a Rex terminal, `zed PATH` opens Zed on the machine the terminal is
# being used from, over SSH back to this one, when that is another
# machine. zed_remote.py makes that call and exits 10 when the Rex app is
# on this machine, in which case the real zed runs. Outside Rex `zed` is
# left alone.
if [ -n "${REX_SESSION:-}" ]; then
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
