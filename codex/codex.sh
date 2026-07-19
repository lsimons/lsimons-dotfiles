# Wrap Codex so the sbp.ai LiteLLM API key is fetched from 1Password
# just before launch instead of sitting in a var or file. Requires `op`
# signed in (see the 1password topic).
codex() {
  local api_key
  api_key=$(OP_ACCOUNT=schubergphilis op read "op://Employee/litellm-pat/token") || return 1
  [ -n "$api_key" ] || return 1
  OPENAI_API_KEY="$api_key" command codex "$@"
}
