# ============================================================================
# Setup: HOST-ONLY dev shell environment                                 BEGIN
# ============================================================================


# 01 =========================================================================
# Raise ulimits per tty session
ulimit -n 65536

# 02 =========================================================================
# SSH agent: starts if one isn't available; loads key if necessary.
if [[ -z "$SSH_AUTH_SOCK" ]] && command -v ssh-agent >/dev/null; then
  eval "$(ssh-agent -s)" >/dev/null
fi
ssh-add -l >/dev/null 2>&1 || ssh-add ~/.ssh/{sign,github}

# 03 =========================================================================
# dev container

# list aliases
alias 'dev?'='alias | grep "dco "'

# access
alias devdc='dco   -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env'

# status
alias devps='dco   -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env \
  ps'

# up
alias devup='dco   -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env \
  up -d --no-recreate'
# rebuild & up
alias devub='dco   -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env \
  up -d --build'

# down
alias devdown='dco -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env \
  down'

# shell
alias dx='dco      -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env \
  exec dev zsh'

alias dev='devup && devps && dx'


# ============================================================================
# END                                                                    Setup
# ============================================================================
