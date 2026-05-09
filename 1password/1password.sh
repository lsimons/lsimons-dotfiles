# 1Password CLI integration
# Cache-first secret loading with 24-hour TTL
#
# Source of truth: ~/.config/1password/secrets-loader.sh — generated
# by 1password/install.py from the base .env.1password plus
# machines/<host>.json's `1password.secrets` map. Each entry resolves
# with an explicit `op read --account <acct>` so secrets from
# different 1Password accounts can coexist on the same machine.

_op_cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/1password"
_op_cache_file="$_op_cache_dir/secrets.sh"
_op_loader_file="${XDG_CONFIG_HOME:-$HOME/.config}/1password/secrets-loader.sh"

# Load cached secrets if cache exists and is less than 24 hours old
_op_cache_valid=0
if [ -f "$_op_cache_file" ]; then
  _op_cache_mtime=$(stat -f %m "$_op_cache_file" 2>/dev/null)
  _op_now=$(date +%s)
  if [ -n "$_op_cache_mtime" ] && [ $((_op_now - _op_cache_mtime)) -lt 86400 ]; then
    _op_cache_valid=1
  fi
fi

if [ "$_op_cache_valid" -eq 1 ]; then
  . "$_op_cache_file"
elif command -v op > /dev/null 2>&1 && [ -f "$_op_loader_file" ]; then
  # Resolve secrets one at a time so each can target its own
  # 1Password account. The loader file calls _op_load per secret;
  # _op_load appends an `export` line to a temp file, which we move
  # into place atomically once the loader finishes.
  _op_tmp=$(mktemp "${TMPDIR:-/tmp}/1password-secrets.XXXXXX" 2>/dev/null) \
    || _op_tmp="${TMPDIR:-/tmp}/1password-secrets.$$"
  : > "$_op_tmp"
  _op_load() {
    # _op_load VAR_NAME ACCOUNT REF
    _op_val=$(op read --account "$2" "$3" 2>/dev/null) || _op_val=""
    if [ -n "$_op_val" ]; then
      printf 'export %s=%q\n' "$1" "$_op_val" >> "$_op_tmp"
    fi
    unset _op_val
  }
  . "$_op_loader_file"
  unset -f _op_load 2>/dev/null || true
  if [ -s "$_op_tmp" ]; then
    mkdir -p "$_op_cache_dir"
    mv "$_op_tmp" "$_op_cache_file"
    chmod 600 "$_op_cache_file"
    . "$_op_cache_file"
  else
    rm -f "$_op_tmp"
  fi
  unset _op_tmp
fi

unset _op_cache_dir _op_cache_file _op_loader_file _op_cache_valid _op_cache_mtime _op_now

# Helper functions for ad-hoc terminal use.
# Both accept an optional --account flag; otherwise they rely on
# whatever 1Password sign-in state is active.
if command -v op > /dev/null 2>&1; then
  # Load a single secret from 1Password
  # Usage: op_load_secret [--account NAME] "op://vault/item/field"
  op_load_secret() {
    if [ "$1" = "--account" ] && [ -n "$2" ]; then
      op read --account "$2" "$3" 2>/dev/null
    elif [ -n "$1" ]; then
      op read "$1" 2>/dev/null
    else
      echo "Usage: op_load_secret [--account NAME] <secret-reference>" >&2
      return 1
    fi
  }

  # Set environment variable from 1Password
  # Usage: op_export [--account NAME] VAR_NAME "op://vault/item/field"
  op_export() {
    local _acct=""
    if [ "$1" = "--account" ]; then
      _acct="$2"
      shift 2
    fi
    if [ -z "$1" ] || [ -z "$2" ]; then
      echo "Usage: op_export [--account NAME] VAR_NAME <secret-reference>" >&2
      return 1
    fi
    local value
    if [ -n "$_acct" ]; then
      value=$(op read --account "$_acct" "$2" 2>/dev/null)
    else
      value=$(op read "$2" 2>/dev/null)
    fi
    if [ -n "$value" ]; then
      export "$1"="$value"
      return 0
    else
      echo "Failed to load secret for $1" >&2
      return 1
    fi
  }
fi
