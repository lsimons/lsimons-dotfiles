#!/usr/bin/env python3
"""
Installation script for lsimons-dotfiles
This script is safe to run multiple times (idempotent)

Supports macOS and Arch-based Linux (Omarchy).

Steps:
1. Bootstrap the platform package manager and a modern Python
   (Homebrew + python@3 on macOS; pacman prerequisites + yay on Arch)
2. Create ~/.dotfiles symlink
3. Setup XDG directories
4. Run topic-specific installation scripts (each installs its own symlinks)

Topics that only make sense on one platform declare that in a
``platforms.txt`` file next to their ``install.py``; topics without one
run everywhere. Unsupported topics are skipped, and any dependency on a
skipped topic is dropped rather than treated as an error.

Pass --dry-run to preview without touching the system. The flag is
propagated to each topic installer.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Checked before importing helpers, which imports tomllib (new in 3.11).
# macOS ships Python 3.9.6 in the Command Line Tools, so on a genuinely
# fresh machine this script would otherwise die on an opaque
# `ModuleNotFoundError: No module named 'tomllib'` before reaching step 2
# above — the step that installs a newer Python. Fail with an instruction
# instead.
#
# Only the standard library sets this floor: the syntax here is still
# 3.9-compatible, so this guard itself parses on the stock interpreter
# and can report the problem.
MIN_PYTHON = (3, 11)
if sys.version_info < MIN_PYTHON:
    if platform.system() == 'Darwin':
        _hint = (
            "Install a newer Python first, then re-run this script:\n"
            "  brew install python\n"
            "If Homebrew is not installed yet either, install it first -- see\n"
            "https://brew.sh. This script installs Homebrew itself, but cannot\n"
            "get far enough to do so on this interpreter.\n"
        )
    else:
        _hint = (
            "Install a newer Python first, then re-run this script:\n"
            "  sudo pacman -S python\n"
        )
    sys.stderr.write(
        f"lsimons-dotfiles needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer, "
        f"but this is {platform.python_version()}.\n"
        f"  interpreter: {sys.executable}\n"
        + _hint
    )
    raise SystemExit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import (
    IS_ARCH,
    IS_LINUX,
    IS_MACOS,
    PLATFORM,
    dry,
    is_dry_run,
    set_dry_run,
)


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def info(message):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def warn(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")


def error(message):
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def run_command(cmd, check=True, capture_output=False, shell=False):
    """Run a shell command and return result"""
    try:
        if shell:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=capture_output,
                text=True
            )
        else:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True
            )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            error(f"Command failed: {cmd}")
            error(f"Exit code: {e.returncode}")
            if e.stderr:
                error(f"Error: {e.stderr}")
            raise
        return e


def check_platform():
    """Verify we're on a supported platform (macOS or Arch-based Linux).

    Anything else still installs — the config-only topics are portable —
    but the package-installing ones have no package manager to reach for,
    so confirm first. In dry-run mode nothing is confirmed, because CI
    runs this on an Ubuntu runner that is deliberately neither.
    """
    if IS_MACOS:
        success("Running on macOS")
        return
    if IS_LINUX:
        if IS_ARCH:
            success("Running on Arch-based Linux")
            return
        warn("This is Linux, but not an Arch derivative")
        warn("Topics that install packages expect pacman/yay and will fail")
    else:
        warn("These dotfiles target macOS and Arch-based Linux")
        warn(f"Detected: {platform.system()}")

    if is_dry_run():
        dry(f"unsupported platform '{PLATFORM}' OK for dry-run")
        return
    response = input("Continue anyway? (y/N): ")
    if response.lower() != 'y':
        info("Installation cancelled")
        sys.exit(0)


def check_homebrew():
    """Check if Homebrew is installed"""
    return shutil.which('brew') is not None


def install_homebrew():
    """Install Homebrew if not present"""
    info("Checking for Homebrew...")

    if is_dry_run():
        dry("assume Homebrew is installed; skipping bootstrap")
        return True

    if check_homebrew():
        success("Homebrew is already installed")
        info(f"Homebrew location: {shutil.which('brew')}")
        return True

    info("Installing Homebrew...")
    info("This may take several minutes and will require your password")

    # Homebrew installation command
    install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'

    try:
        run_command(install_cmd, shell=True)
        success("Homebrew installed successfully")

        # Add Homebrew to PATH for this session
        if platform.machine() == 'arm64':
            # Apple Silicon
            brew_path = '/opt/homebrew/bin'
        else:
            # Intel
            brew_path = '/usr/local/bin'

        if brew_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = f"{brew_path}:{os.environ['PATH']}"
            info(f"Added {brew_path} to PATH for this session")

        return True
    except subprocess.CalledProcessError:
        error("Failed to install Homebrew")
        return False


def check_homebrew_python():
    """Check if Python is installed via Homebrew"""
    if not check_homebrew():
        return False

    result = run_command(
        ['brew', 'list', 'python@3'],
        check=False,
        capture_output=True
    )
    return result.returncode == 0


def install_python():
    """Install Python via Homebrew"""
    info("Checking for Homebrew Python...")

    if is_dry_run():
        dry("assume Homebrew python@3 is installed; skipping bootstrap")
        return True

    if check_homebrew_python():
        success("Python is already installed via Homebrew")
        python_path = get_homebrew_python()
        info(f"Python location: {python_path}")

        # Get Python version
        result = run_command([python_path, '--version'], capture_output=True)
        python_version = result.stdout.strip()
        info(f"Python version: {python_version}")
        return True

    info("Installing Python via Homebrew...")

    try:
        run_command(['brew', 'install', 'python@3'])
        success("Python installed successfully")

        # Verify installation
        python_path = get_homebrew_python()
        result = run_command([python_path, '--version'], capture_output=True)
        python_version = result.stdout.strip()
        success(f"Installed: {python_version}")

        return True
    except subprocess.CalledProcessError:
        error("Failed to install Python")
        return False


def get_homebrew_python():
    """Get the path to Homebrew Python"""
    if is_dry_run():
        return sys.executable
    result = run_command(['brew', '--prefix', 'python@3'], capture_output=True)
    return str(Path(result.stdout.strip()) / 'bin' / 'python3')


# Packages every Arch install needs before the first topic installer runs:
# base-devel and git are what yay needs to build anything from the AUR, and
# python is the interpreter the topic installers run under.
LINUX_BOOTSTRAP_PACKAGES = ['base-devel', 'git', 'python']


def pacman_has(package):
    """True if `package` is installed locally (pacman -Qi)."""
    result = run_command(
        ['pacman', '-Qi', package], check=False, capture_output=True
    )
    return result.returncode == 0


def bootstrap_linux():
    """Install the pacman prerequisites and yay, the AUR helper.

    Unlike the macOS bootstrap this cannot install its own package
    manager: pacman comes with the distro. A non-Arch Linux is therefore
    a warning rather than a failure — config-only topics still work
    there, which is what keeps `--dry-run` meaningful on the CI runner.
    """
    info("Checking Arch package prerequisites...")

    if is_dry_run():
        dry("assume pacman prerequisites and yay are installed; skipping bootstrap")
        return True

    if shutil.which('pacman') is None:
        warn("pacman not found; skipping the Arch package bootstrap")
        warn("Topics that install packages will fail on this system")
        return True

    missing = [pkg for pkg in LINUX_BOOTSTRAP_PACKAGES if not pacman_has(pkg)]
    if missing:
        info(f"Installing prerequisites: {', '.join(missing)}")
        try:
            run_command(
                ['sudo', 'pacman', '-S', '--needed', '--noconfirm', *missing]
            )
        except subprocess.CalledProcessError:
            error("Failed to install Arch prerequisites")
            return False
        success("Arch prerequisites installed")
    else:
        success("Arch prerequisites already installed")

    if shutil.which('yay') is not None:
        success("yay already installed")
        return True

    info("Installing yay (AUR helper)...")
    try:
        run_command(['sudo', 'pacman', '-S', '--needed', '--noconfirm', 'yay'])
        success("yay installed")
    except subprocess.CalledProcessError:
        warn("Could not install yay from a configured repository")
        warn("AUR-only packages will fail; see https://github.com/Jguer/yay")

    return True


def bootstrap_platform():
    """Install the platform package manager and a modern Python.

    Returns the interpreter path the topic installers should run under,
    or None if the bootstrap failed.
    """
    if IS_MACOS:
        if not install_homebrew():
            error("Homebrew installation failed. Cannot continue.")
            return None
        if not install_python():
            error("Python installation failed. Cannot continue.")
            return None
        return get_homebrew_python()

    if IS_LINUX:
        if not bootstrap_linux():
            return None
        # pacman's `python` is current (Arch is a rolling release) and the
        # guard at the top of this file has already vetted this
        # interpreter, so there is nothing to install a newer one *for*.
        return sys.executable

    warn(f"No package-manager bootstrap for platform '{PLATFORM}'")
    return sys.executable


def create_dotfiles_symlink(dotfiles_root):
    """Create ~/.dotfiles symlink if it doesn't already exist"""
    home = Path.home()
    symlink_path = home / '.dotfiles'

    info("Setting up ~/.dotfiles symlink...")

    # Check if symlink already exists and points to the correct location
    if symlink_path.is_symlink():
        current_target = symlink_path.resolve()
        if current_target == dotfiles_root:
            success("~/.dotfiles symlink already points to correct location")
            return True
        else:
            warn(f"~/.dotfiles exists but points to: {current_target}")
            warn(f"Expected: {dotfiles_root}")
            if is_dry_run():
                dry("would prompt to recreate ~/.dotfiles symlink")
                return True
            response = input("Remove and recreate symlink? (y/N): ")
            if response.lower() != 'y':
                info("Skipping symlink creation")
                return False
            symlink_path.unlink()

    # Check if a regular directory exists at ~/.dotfiles
    elif symlink_path.exists():
        error("~/.dotfiles exists as a directory or file, not a symlink")
        error(f"Please move or remove {symlink_path} manually")
        return False

    if is_dry_run():
        dry(f"would create symlink ~/.dotfiles -> {dotfiles_root}")
        return True

    # Create the symlink
    try:
        symlink_path.symlink_to(dotfiles_root)
        success(f"Created symlink: ~/.dotfiles -> {dotfiles_root}")
        return True
    except Exception as e:  # noqa: BLE001 - report any symlink failure, keep going
        error(f"Failed to create symlink: {e}")
        return False


def setup_xdg():
    """Setup XDG Base Directory structure"""
    info("Setting up XDG Base Directory structure...")

    home = Path.home()
    xdg_config_home = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
    xdg_data_home = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share'))
    xdg_cache_home = Path(os.environ.get('XDG_CACHE_HOME', home / '.cache'))
    xdg_state_home = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state'))

    if is_dry_run():
        for p in (xdg_config_home, xdg_data_home, xdg_cache_home, xdg_state_home):
            dry(f"would mkdir {p}")
        return

    xdg_config_home.mkdir(parents=True, exist_ok=True)
    xdg_data_home.mkdir(parents=True, exist_ok=True)
    xdg_cache_home.mkdir(parents=True, exist_ok=True)
    xdg_state_home.mkdir(parents=True, exist_ok=True)

    success("XDG directories created")


# Topics that must run after all others, in this exact order. They are
# excluded from the normal dependency-sorted pass and run last so the apps
# and tools they reference are guaranteed to be installed first.
FINAL_TOPICS = ['dock']


def _read_list_file(path):
    """Read a one-entry-per-line config file, ignoring blanks and comments."""
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            entries.append(line)
    return entries


def get_topic_dependencies(topic_dir):
    """Read dependencies from a topic's dependencies.txt file"""
    return _read_list_file(topic_dir / 'dependencies.txt')


def get_topic_platforms(topic_dir):
    """Read the platforms a topic supports from its platforms.txt file.

    Returns None when the file is absent, which means "every platform" —
    that is the case for the large majority of topics, so only the ones
    that are genuinely platform-bound need to say anything.
    """
    platforms_file = topic_dir / 'platforms.txt'
    if not platforms_file.exists():
        return None
    return set(_read_list_file(platforms_file))


def topic_supported(topic_dir):
    """True if this topic should be installed on the current platform."""
    platforms = get_topic_platforms(topic_dir)
    return platforms is None or PLATFORM in platforms


def topological_sort(topics, dependencies):
    """
    Sort topics so dependencies come before dependents.
    topics: dict of topic_name -> install_script_path
    dependencies: dict of topic_name -> list of dependency topic names
    Returns: list of topic names in installation order
    """
    unknown = sorted(
        (topic, dep)
        for topic, deps in dependencies.items()
        for dep in deps
        if dep not in topics
    )
    if unknown:
        for topic, dep in unknown:
            error(f"Topic '{topic}' depends on unknown topic '{dep}'")
        return None

    # Build in-degree map and adjacency list
    in_degree = {topic: 0 for topic in topics}
    dependents = {topic: [] for topic in topics}

    for topic, deps in dependencies.items():
        for dep in deps:
            in_degree[topic] += 1
            dependents[dep].append(topic)

    # Kahn's algorithm for topological sort
    queue = [topic for topic, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        # Sort queue for deterministic ordering
        queue.sort()
        topic = queue.pop(0)
        result.append(topic)

        for dependent in dependents[topic]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(topics):
        # Cycle detected
        remaining = set(topics.keys()) - set(result)
        error(f"Circular dependency detected involving: {remaining}")
        return None

    return result


def run_topic_installers(dotfiles_root, python_path):
    """Run topic-specific installation scripts in dependency order"""
    info("Looking for topic installation scripts...")

    topics = {}  # topic_name -> install_script_path
    dependencies = {}  # topic_name -> list of dependencies
    skipped = []  # topic names excluded on this platform

    # Find all install.py scripts and their dependencies
    for topic_dir in dotfiles_root.iterdir():
        # Skip script directory to avoid recursive invocation
        if (topic_dir.is_dir()
                and not topic_dir.name.startswith('.')
                and topic_dir.name != 'script'
                and topic_dir.name not in FINAL_TOPICS):
            install_py = topic_dir / 'install.py'
            if install_py.exists():
                topic_name = topic_dir.name
                if not topic_supported(topic_dir):
                    skipped.append(topic_name)
                    continue
                topics[topic_name] = install_py
                dependencies[topic_name] = get_topic_dependencies(topic_dir)

    if skipped:
        info(
            f"Skipping {len(skipped)} topic(s) not supported on {PLATFORM}: "
            f"{', '.join(sorted(skipped))}"
        )

    # A dependency on a topic that is skipped on this platform is not an
    # error: the dependent topic just loses an ordering constraint it no
    # longer needs. Dropping it here keeps topological_sort's genuine
    # "depends on a topic that does not exist" check meaningful.
    skipped_set = set(skipped)
    for topic_name, deps in dependencies.items():
        dropped = [dep for dep in deps if dep in skipped_set]
        if dropped:
            info(
                f"{topic_name}: dropping dependency on "
                f"{', '.join(sorted(dropped))} (skipped on {PLATFORM})"
            )
            dependencies[topic_name] = [d for d in deps if d not in skipped_set]

    if not topics:
        info("No topic install.py scripts found")
        return True

    info(f"Found {len(topics)} topic installer(s)")

    # Sort topics by dependencies
    sorted_topics = topological_sort(topics, dependencies)
    if sorted_topics is None:
        return False

    child_args = ['--dry-run'] if is_dry_run() else []

    # Run each installer in order
    for topic in sorted_topics:
        script = topics[topic]
        deps = dependencies[topic]
        if deps:
            info(f"Running installer for: {topic} (depends on: {', '.join(deps)})")
        else:
            info(f"Running installer for: {topic}")

        try:
            run_command([python_path, str(script), *child_args])
            success(f"Installed: {topic}")
        except subprocess.CalledProcessError:
            error(f"Failed to install: {topic}")
            return False

    return True


def run_final_topics(dotfiles_root, python_path):
    """Run the FINAL_TOPICS installers last, in declared order."""
    child_args = ['--dry-run'] if is_dry_run() else []

    for topic in FINAL_TOPICS:
        topic_dir = dotfiles_root / topic
        script = topic_dir / 'install.py'
        if not script.exists():
            continue
        if not topic_supported(topic_dir):
            info(f"Skipping final topic {topic}: not supported on {PLATFORM}")
            continue
        info(f"Running final installer for: {topic}")
        try:
            run_command([python_path, str(script), *child_args])
            success(f"Installed: {topic}")
        except subprocess.CalledProcessError:
            error(f"Failed to install: {topic}")
            return False

    return True


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print what would happen without making any changes.',
    )
    return parser.parse_args(argv)


def main():
    """Main installation flow"""
    args = parse_args()
    set_dry_run(args.dry_run)

    info("Starting lsimons-dotfiles installation")
    if is_dry_run():
        dry("dry-run mode: no changes will be made")
    info("=" * 50)

    # Get dotfiles root directory
    script_dir = Path(__file__).resolve().parent
    dotfiles_root = script_dir.parent.resolve()
    info(f"Dotfiles root: {dotfiles_root}")

    # Step 1: Check the platform
    check_platform()

    # Step 2: Bootstrap the package manager and a modern Python
    python_path = bootstrap_platform()
    if python_path is None:
        sys.exit(1)
    success(f"Using Python: {python_path}")

    # Step 3: Create ~/.dotfiles symlink
    info("=" * 50)
    if not create_dotfiles_symlink(dotfiles_root):
        error("Failed to create ~/.dotfiles symlink")
        sys.exit(1)

    # Step 4: Setup XDG directories
    setup_xdg()

    # Step 5: Add mise shims to PATH so topic installers can find mise-managed
    # tools (e.g. npm) even before the shell config topics have been sourced.
    xdg_data_home = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    mise_shims = str(xdg_data_home / 'mise' / 'shims')
    if mise_shims not in os.environ.get('PATH', '').split(':'):
        os.environ['PATH'] = f"{mise_shims}:{os.environ['PATH']}"
        info(f"Added mise shims to PATH: {mise_shims}")

    # Step 6: Run topic installers (each installs its own .symlink files)
    info("=" * 50)
    if not run_topic_installers(dotfiles_root, python_path):
        error("Some topic installations failed")
        sys.exit(1)

    # Step 7: Run final topics (e.g. dock) after everything else
    if not run_final_topics(dotfiles_root, python_path):
        error("Some topic installations failed")
        sys.exit(1)

    # Done
    success("=" * 50)
    if is_dry_run():
        success("Dry-run complete. No changes made.")
    else:
        success("Installation complete!")
        info("")
        info("Next steps:")
        info("  1. Restart your shell (or 'source ~/.zshrc') to load the config")
        info("  2. Configure 1Password CLI for secret management")
        if IS_LINUX:
            info("  3. Enable the 1Password SSH agent in the desktop app's")
            info("     Developer settings, so git commit signing works")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        warn("Installation cancelled by user")
        sys.exit(130)
    except Exception as e:  # noqa: BLE001 - top-level catch-all for clean exit
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
