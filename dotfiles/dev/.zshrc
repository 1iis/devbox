# ============================================================================
# DEV .zshrc
# ============================================================================
# > SHARED with dev@dev


# 00 =========================================================================
# Powerlevel10k
# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi


# 01 =========================================================================
# Add directory for user binaries.
typeset -U path && path=("$HOME/bin" "$HOME/.local/bin" $path) && export PATH


# 02 =========================================================================
# Zsh + Oh-my-Zsh!
disable log    # this is math.log (lol)
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
source ~/.oh-my-zsh/custom/history.zsh
CASE_SENSITIVE="true"
zstyle ':omz:update' mode reminder
ENABLE_CORRECTION="false" # sometimes messes up with correct commands
COMPLETION_WAITING_DOTS="true"
DISABLE_UNTRACKED_FILES_DIRTY="true"
HIST_STAMPS="yyyy-mm-dd"
plugins=(
  aliases sudo cp ufw ssh systemd docker docker-compose git pip uv
  zsh-autosuggestions zsh-syntax-highlighting
)
source $ZSH/oh-my-zsh.sh


# 03 =========================================================================
# fzf
[ -f /usr/share/fzf/completion.zsh ] && source /usr/share/fzf/completion.zsh
[ -f /usr/share/fzf/key-bindings.zsh ] && source /usr/share/fzf/key-bindings.zsh


# 04 =========================================================================
# Powerlevel10k
# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
typeset -g POWERLEVEL9K_INSTANT_PROMPT=quiet


# 05 =========================================================================
# 1init
echo -e "$(date) $(?@?)" | grep "dev"


# ============================================================================
# END                                                               DEV .zshrc
# ============================================================================
