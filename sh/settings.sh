# General shell settings

export LANG=en_US.UTF-8

# Preferred editor: the first one actually installed wins. Zed is the
# daily driver, but its Linux binary is named `zeditor`, and there is no
# aarch64 build at all — so fall back to a terminal editor rather than
# export an EDITOR that cannot be launched.
for _dotfiles_editor in "zed -w" "zeditor -w" nvim vim; do
  if command -v "${_dotfiles_editor%% *}" >/dev/null 2>&1; then
    export EDITOR="$_dotfiles_editor"
    break
  fi
done
unset _dotfiles_editor

# Silence macOS "default interactive shell is now zsh" warning.
# Must be set in the parent environment before bash starts.
case "$OSTYPE" in
  darwin*) export BASH_SILENCE_DEPRECATION_WARNING=1 ;;
esac
