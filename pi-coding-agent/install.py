#!/usr/bin/env python3
"""Installation script for pi-coding-agent"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    print("[INFO] Installing pi-coding-agent...")

    # Check if npm is available (requires Node.js to be installed)
    result = subprocess.run(['which', 'npm'], capture_output=True)
    if result.returncode != 0:
        # Try to source nvm and check again
        xdg_data_home = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))
        nvm_dir = Path(xdg_data_home) / 'nvm'

        if not (nvm_dir / 'nvm.sh').exists():
            print("[ERROR] npm not found. Please install Node.js first (run node/install.py)", file=sys.stderr)
            return 1

    # Check if already installed
    check_script = '''
        export NVM_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
        which pi 2>/dev/null
    '''
    result = subprocess.run(['bash', '-c', check_script], capture_output=True)
    if result.returncode == 0:
        print("[SUCCESS] pi-coding-agent already installed")
        return 0

    # Install via npm globally
    try:
        install_script = '''
            export NVM_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
            npm install -g @mariozechner/pi-coding-agent
        '''
        subprocess.run(['bash', '-c', install_script], check=True)
        print("[SUCCESS] pi-coding-agent installed")
        return 0
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install pi-coding-agent", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
