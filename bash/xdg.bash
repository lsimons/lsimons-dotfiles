# Bash-specific XDG configuration

export HISTFILE="$XDG_STATE_HOME/bash/history"
export HISTSIZE=10000
export HISTFILESIZE=10000

# Ensure Bash state directory exists
mkdir -p "$(dirname "$HISTFILE")"
