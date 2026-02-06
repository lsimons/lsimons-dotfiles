# XDG Base Directory configuration
# Follow https://specifications.freedesktop.org/basedir-spec/latest/

# Ensure XDG directories exist
mkdir -p "$XDG_CONFIG_HOME"
mkdir -p "$XDG_DATA_HOME"
mkdir -p "$XDG_CACHE_HOME"
mkdir -p "$XDG_STATE_HOME"

# Configure Bash to use XDG paths
export HISTFILE="$XDG_STATE_HOME/bash/history"
export HISTSIZE=10000
export HISTFILESIZE=10000

# Ensure Bash state directory exists
mkdir -p "$(dirname "$HISTFILE")"
