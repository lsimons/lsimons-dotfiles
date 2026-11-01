# General shell settings

export LANG=en_US.UTF-8

# Preferred editor: the first one actually installed wins. micro comes
# first because it runs inside the terminal: over a remote terminal
# session (Rex remoting, ssh) a GUI editor like Zed opens on whichever
# machine runs the shell, not in front of you. Zed stays as a fallback
# (its Linux binary is `zeditor`), then nvim and vim.
#
# VISUAL and GIT_EDITOR get the same value so nothing falls back to its
# own default: git checks GIT_EDITOR before core.editor, and many tools
# prefer VISUAL over EDITOR.
for _dotfiles_editor in micro "zed -w" "zeditor -w" nvim vim; do
  if command -v "${_dotfiles_editor%% *}" >/dev/null 2>&1; then
    export EDITOR="$_dotfiles_editor"
    export VISUAL="$_dotfiles_editor"
    export GIT_EDITOR="$_dotfiles_editor"
    break
  fi
done
unset _dotfiles_editor

# Silence macOS "default interactive shell is now zsh" warning.
# Must be set in the parent environment before bash starts.
case "$OSTYPE" in
  darwin*) export BASH_SILENCE_DEPRECATION_WARNING=1 ;;
esac

# XDG Base Directory configuration
# Follow https://specifications.freedesktop.org/basedir-spec/latest/

# Ensure XDG directories exist
mkdir -p "$XDG_CONFIG_HOME"
mkdir -p "$XDG_DATA_HOME"
mkdir -p "$XDG_CACHE_HOME"
mkdir -p "$XDG_STATE_HOME"
