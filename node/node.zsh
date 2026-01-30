# nvm (Node Version Manager) configuration
# XDG-compliant nvm directory
export NVM_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nvm"

# Load nvm
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Load nvm bash completion
[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
