#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# ── Collect identity ──────────────────────────────────────────────
NAME="${NAME:-}"
EMAIL="${EMAIL:-}"
SSH_SIGN_KEY="${SSH_SIGN_KEY:-$HOME/.ssh/sign}"
SSH_PRIVATE_KEY="${SSH_PRIVATE_KEY:-$HOME/.ssh/dev}"

echo "== devbox setup =="
echo

# NAME
while [ -z "$NAME" ]; do
  read -r -p "Name for Git config: " NAME
done

# EMAIL
while [ -z "$EMAIL" ]; do
  read -r -p "Email for Git config: " EMAIL
done

# SSH signing key
read -r -p "SSH signing private key [$SSH_SIGN_KEY]: " ans
SSH_SIGN_KEY="${ans:-$SSH_SIGN_KEY}"

# SSH auth private key
read -r -p "SSH auth private key [$SSH_PRIVATE_KEY]: " ans
SSH_PRIVATE_KEY="${ans:-$SSH_PRIVATE_KEY}"

echo
echo "  Name:            $NAME"
echo "  Email:           $EMAIL"
echo "  SSH sign key:    $SSH_SIGN_KEY"
echo "  SSH auth key:    $SSH_PRIVATE_KEY"
echo

# ── Write env.zsh ─────────────────────────────────────────────────
ENV_DST="dotfiles/dev/.oh-my-zsh/custom/env.zsh"
mkdir -p "$(dirname "$ENV_DST")"
sed \
  -e "s|\$NAME|$NAME|g" \
  -e "s|\$EMAIL|$EMAIL|g" \
  -e "s|\$SSH_SIGN_KEY|${SSH_SIGN_KEY}|g" \
  -e "s|\$SSH_PRIVATE_KEY|${SSH_PRIVATE_KEY}|g" \
  templates/env.zsh.example > "$ENV_DST"
echo "✓ env.zsh written"

# ── Compile sync.py ───────────────────────────────────────────────
python3 -m py_compile host/sync.py
echo "✓ host/sync.py compiles"

# ── Install make if missing ───────────────────────────────────────
if ! command -v make &>/dev/null; then
  echo "  installing make…"
  sudo apt-get update -qq && sudo apt-get install -y -qq make
  echo "✓ make installed"
fi

# ── Prepare flags ─────────────────────────────────────────────────
FLAGS="--name \"$NAME\" --email \"$EMAIL\""
[ -n "$SSH_SIGN_KEY" ]    && FLAGS="$FLAGS --ssh-sign-key \"$SSH_SIGN_KEY\""
[ -n "$SSH_PRIVATE_KEY" ] && FLAGS="$FLAGS --ssh-private-key \"$SSH_PRIVATE_KEY\""

# ── Dry run ───────────────────────────────────────────────────────
echo
echo "== Dry run (status) =="
eval "python3 host/sync.py status $FLAGS"
echo

# ── Converge ──────────────────────────────────────────────────────
read -r -p "Converge host now? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Aborted."
  exit 1
fi

echo
echo "== Enabling devbox =="
eval "sudo python3 host/sync.py enable $FLAGS"

echo
echo "✓ devbox installed"
echo
echo "Next: sudo -iu dev"
echo "Then: cd ~/.devbox && ./scripts/dev-in.sh"
