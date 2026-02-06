# Bash-it configuration
# Loaded early to set up prompt, aliases, and completions

BASH_IT="${XDG_DATA_HOME:-$HOME/.local/share}/bash-it"

if [ -d "$BASH_IT" ]; then
    export BASH_IT
    export BASH_IT_THEME='robbyrussell'

    # Enable git plugin and completion
    SCM_CHECK=true

    source "${BASH_IT}/bash_it.sh"
fi
