# Terminal tools configuration. Loaded from .zshrc.
[[ -o interactive ]] || return 0
[[ -z ${_kael_terminal_loaded-} ]] || return 0
typeset -g _kael_terminal_loaded=1
typeset -g _kael_config="${XDG_CONFIG_HOME:-$HOME/.config}"
typeset -g _kael_data="${XDG_DATA_HOME:-$HOME/.local/share}"

typeset -U path PATH
path=("$_kael_data/kael-terminal/bin" "$HOME/.local/bin" "$HOME/bin" $path)
[[ ! -r "$HOME/.cargo/env" ]] || source "$HOME/.cargo/env"
export EDITOR="${EDITOR:-vim}"

HISTFILE="$HOME/.zsh_history"
HISTSIZE=50000
SAVEHIST=50000
setopt APPEND_HISTORY SHARE_HISTORY HIST_IGNORE_DUPS HIST_IGNORE_SPACE
bindkey -e

autoload -Uz compinit
compinit
zstyle ':completion:*' menu select

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
if (( $+commands[eza] )); then
  alias lt='eza --tree --level=2 --icons=auto'
  alias lgit='eza -al --git --icons=auto'
fi

# Apply the directory that Yazi reports on exit to the current shell.
unalias yazi 2>/dev/null || :
function yazi() {
  local arg tmp cwd result=0
  for arg in "$@"; do
    case "$arg" in
      --cwd-file|--cwd-file=*)
        command env -u TERM_PROGRAM -u TABBY_CONFIG_DIRECTORY yazi "$@"
        return $?
        ;;
      --) break ;;
    esac
  done

  tmp="$(mktemp -t yazi-cwd.XXXXXX)" || return
  command env -u TERM_PROGRAM -u TABBY_CONFIG_DIRECTORY yazi --cwd-file="$tmp" "$@" || result=$?
  IFS= read -r -d '' cwd < "$tmp" || :
  if [[ "$cwd" != "$PWD" && -d "$cwd" ]]; then
    builtin cd -- "$cwd" || :
  fi
  command rm -f -- "$tmp"
  return "$result"
}
alias y='yazi'

# Conda uses its Zsh hook; Bash startup files are not sourced here.
if [[ -x "$HOME/anaconda3/bin/conda" ]]; then
  __terminal_conda_setup="$("$HOME/anaconda3/bin/conda" shell.zsh hook 2>/dev/null)"
  if (( $? == 0 )); then
    eval "$__terminal_conda_setup"
  elif [[ -r "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
  fi
  unset __terminal_conda_setup
fi

if (( $+commands[zoxide] )); then
  eval "$(zoxide init zsh)"
fi
if (( $+commands[starship] )); then
  export STARSHIP_CONFIG="${STARSHIP_CONFIG:-$_kael_config/starship.toml}"
  eval "$(starship init zsh)"
else
  PROMPT='%F{green}%n@%m%f:%F{blue}%~%f %# '
fi

[[ ! -r /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]] ||
  source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh

if (( $+commands[atuin] )); then
  eval "$(atuin init zsh)"
fi

if (( $+commands[fzf] )); then
  FZF_CTRL_R_COMMAND= FZF_ALT_C_COMMAND= source <(fzf --zsh)
  bindkey '^I' expand-or-complete
fi

# Use a dedicated socket outside tmux and keep commands on the same socket inside it.
if [[ -x "${KAEL_TMUX_BIN:-$_kael_data/kael-terminal/bin/tmux}" ]]; then
  case "${TMUX-}" in
    ''|*/kael-borders,*|*/kael-borders-sixel,*) alias tmux='kael-tmux' ;;
  esac
fi

function codex() {
  local preview="$_kael_data/kael-terminal/codex-tabby-preview.py"
  if [[ -t 0 && -t 1 && -r "$preview" ]] &&
     [[ ${TERM_PROGRAM:l} == tabby || -n ${TABBY_CONFIG_DIRECTORY-} ||
        ${TMUX-} == */kael-borders-sixel,* ]]; then
    command python3 "$preview" --tabby-default "$@"
  else
    command codex "$@"
  fi
}

[[ ! -r "$_kael_config/kael-terminal/local.zsh" ]] ||
  source "$_kael_config/kael-terminal/local.zsh"

# Load after other plugins that install or modify line-editor widgets.
[[ ! -r /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]] ||
  source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
