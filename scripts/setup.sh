#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# Helpers
say() { printf '%s\n' "$@" >&2; }

# Collect identity
NAME="${NAME:-}"
EMAIL="${EMAIL:-}"
SSH_SIGN_KEY="${SSH_SIGN_KEY:-$HOME/.ssh/sign}"
SSH_PRIVATE_KEY="${SSH_PRIVATE_KEY:-$HOME/.ssh/dev}"

say "== devbox setup =="
say

while [ -z "$NAME" ];  do read -r -p "Name for Git config: "  NAME;  done
while [ -z "$EMAIL" ]; do read -r -p "Email for Git config: " EMAIL; done

# SSH signing key
read -r -p "SSH sign private key [$SSH_SIGN_KEY, Enter to auto-generate if missing]: " ans
SSH_SIGN_KEY="${ans:-$SSH_SIGN_KEY}"
[ -f "$SSH_SIGN_KEY" ] || SSH_SIGN_KEY=""

# SSH auth private key
read -r -p "SSH auth private key [$SSH_PRIVATE_KEY, Enter to auto-generate if missing]: " ans
SSH_PRIVATE_KEY="${ans:-$SSH_PRIVATE_KEY}"
[ -f "$SSH_PRIVATE_KEY" ] || SSH_PRIVATE_KEY=""

say
say "  Name:            $NAME"
say "  Email:           $EMAIL"
say "  SSH sign key:    $SSH_SIGN_KEY"
say "  SSH auth key:    $SSH_PRIVATE_KEY"
say

# Compile sync.py
python3 -m py_compile host/sync.py && say "✓ host/sync.py compiles"

# Install make if missing
# if ! command -v make &>/dev/null; then
#   say "  installing make…"
#   sudo apt-get update -qq && sudo apt-get install -y -qq make
#   say "✓ make installed"
# fi

# Prepare flags
FLAGS=(--name "$NAME" --email "$EMAIL")
[ -n "$SSH_SIGN_KEY" ]    && FLAGS+=(--ssh-sign-key "$SSH_SIGN_KEY")
[ -n "$SSH_PRIVATE_KEY" ] && FLAGS+=(--ssh-private-key "$SSH_PRIVATE_KEY")

# Dry run
say
say "== Dry run (status) =="
python3 host/sync.py status "${FLAGS[@]}" || true
say

# Converge
read -r -p "Converge host now? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  say "Aborted."
  exit 1
fi

say
say "== Enabling devbox =="
sudo python3 host/sync.py enable "${FLAGS[@]}" || true

say
say "✓ devbox installed"
say
say "Next:"
say "  sudo -iu dev"
say "  cd ~/.devbox"
say "  ./scripts/dev-in.sh"
