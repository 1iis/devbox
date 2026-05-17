# ============================================================================
# Docker                                                                 BEGIN
# ============================================================================


# Sugar (cmd = cmd + goodies)
alias up='dcupd --no-recreate && dcps'
alias down='dcdn && dcps'

# Quick commands
alias dv='docker volume'

# Compose Profiles
alias 'dclog'="docker compose --profile ${COMPOSE_PROFILES} logs -f"


# ============================================================================
# END                                                                   Docker
# ============================================================================
