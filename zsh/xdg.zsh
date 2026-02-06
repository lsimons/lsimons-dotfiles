# ZSH-specific XDG configuration

mkdir -p "$XDG_CACHE_HOME/zsh"

# Configure ZSH to use XDG paths
export ZDOTDIR="${ZDOTDIR:-$XDG_CONFIG_HOME/zsh}"
export HISTFILE="$XDG_STATE_HOME/zsh/history"
export HISTSIZE=10000
export SAVEHIST=10000

# Ensure ZSH state directory exists
mkdir -p "$(dirname "$HISTFILE")"
