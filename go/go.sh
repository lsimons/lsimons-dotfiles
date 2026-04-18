# Go configuration following XDG Base Directory specification

export GOPATH="$XDG_DATA_HOME/go"

if [ -d "$GOPATH/bin" ]; then
  export PATH="$GOPATH/bin:$PATH"
fi
