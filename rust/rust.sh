# Rust configuration following XDG Base Directory specification

export RUSTUP_HOME="$XDG_DATA_HOME/rustup"
export CARGO_HOME="$XDG_DATA_HOME/cargo"

if [ -f "$CARGO_HOME/env" ]; then
  . "$CARGO_HOME/env"
fi
