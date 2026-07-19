# Wrap opencode so the sbp.ai LiteLLM API key is fetched from 1Password
# just before launch instead of sitting in a var or file. Requires `op`
# signed in (see the 1password topic).
opencode() {
  SBP_AI_API_KEY=$(OP_ACCOUNT=schubergphilis op read "op://Employee/litellm-pat/token") command opencode "$@"
}
