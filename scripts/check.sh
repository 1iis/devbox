#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== python compile =="
python3 -m py_compile host/sync.py

echo "== sync help =="
python3 host/sync.py --help >/dev/null

echo "== shell syntax =="
for f in scripts/*.sh; do
  bash -n "$f"
done

echo "== compose config =="
SSH_AUTH_SOCK="${SSH_AUTH_SOCK:-/tmp/devbox-ci-ssh-agent.sock}" \
  docker compose -f container/docker-compose.yml --project-directory container config >/dev/null

echo "ok"
