# XDG Base Directory configuration
# Follow https://specifications.freedesktop.org/basedir-spec/latest/

# Ensure XDG directories exist
mkdir -p "$XDG_CONFIG_HOME"
mkdir -p "$XDG_DATA_HOME"
mkdir -p "$XDG_CACHE_HOME"
mkdir -p "$XDG_STATE_HOME"
