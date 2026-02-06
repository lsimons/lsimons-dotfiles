#!/usr/bin/env python3
"""Installation script for Bash-it"""

import subprocess
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'script'))
from helpers import info, success, error


def main():
    info("Installing Bash-it...")

    xdg_data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    bash_it_dir = xdg_data / 'bash-it'

    if bash_it_dir.exists():
        success("Bash-it already installed")
        return 0

    try:
        subprocess.run(
            ['git', 'clone', '--depth=1',
             'https://github.com/Bash-it/bash-it.git',
             str(bash_it_dir)],
            check=True
        )
        success("Bash-it installed")
        return 0
    except subprocess.CalledProcessError:
        error("Failed to install Bash-it")
        return 1


if __name__ == '__main__':
    sys.exit(main())
