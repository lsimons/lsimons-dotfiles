[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

if (( $+commands[brew] )); then
  powerlevel10k_prefix="$(brew --prefix powerlevel10k)"
  [[ ! -r "$powerlevel10k_prefix/share/powerlevel10k/powerlevel10k.zsh-theme" ]] || \
    source "$powerlevel10k_prefix/share/powerlevel10k/powerlevel10k.zsh-theme"
  unset powerlevel10k_prefix
fi
