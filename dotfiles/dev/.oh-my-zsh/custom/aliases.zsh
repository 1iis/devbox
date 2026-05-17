# ============================================================================
# Aliases [all users]                                                    BEGIN
# ============================================================================

# Who and where am I? (colors: blue=dev@host mint=dev@ctn none=other)
# This is a good example of function that can be greatly simplified by making
# it user@host-specific (e.g. following our `10-rc.zsh` pattern).
alias '?@?'='if [ "$HOST" = "dev" ]; then \
    echo -e "\033[38;5;49m$(whoami)@$(hostname):$(pwd)\033[0m"; \
  elif [ "$USER" = "dev" ]; then \
    echo -e "\033[1;36m$(whoami)@$(hostname):$(pwd)\033[0m"; \
  else \
    echo -e "$(whoami)@$(hostname):$(pwd)"; \
  fi'

# ============================================================================
# Shell things

# Fix Ubuntu
alias fd=fdfind
command -v batcat >/dev/null 2>&1 && alias bat=batcat

# 1-char
alias l='ls -FLlAsh'
alias c='cat '
alias b='batcat '
alias e='nano --softwrap --atblanks --constantshow --autoindent --linenumbers '
alias E='sudo nano --softwrap --atblanks --constantshow --autoindent --linenumbers '
alias ','='clear'
alias ',,'='clear && ?@? && l '

# Paths
alias ',g'='cd ~/git'
alias ',p'='cd ~/pj'

# auto-verbosity (pipe to 1>/dev/null to suppress)
alias 'mv'='mv -v '
alias 'cp'='cp -v '
alias 'rm'='rm -v '
alias 'mk'='mkdir -pv '
alias 'rmdir'='rmdir -v '

# quick edit this
alias 'rc'="e $HOME/.zshrc"
alias '__'="e /home/dev/.oh-my-zsh/custom/aliases.zsh"
alias '___'="e $ZSH_CUSTOM/$USER.zsh"
alias 'rel'="source ~/.zshrc"

# eye-candy
alias 'lf'="echo '\n\n'"
alias 'sep'="echo '\n\n\n____________\n\n'"

# ============================================================================
# Utils
alias 'ipget'='curl -4 ipget.io'

# ============================================================================
# SSH
# kitty
alias kssh='kitty +kitten ssh '

# ============================================================================
# END                                                                  Aliases
# ============================================================================
