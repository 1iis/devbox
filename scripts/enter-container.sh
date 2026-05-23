#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="${DEVBOX_RUN_DIR:-/home/dev/.config/dev-env}"

docker compose -f "$RUN_DIR/docker-compose.yml" --project-directory "$RUN_DIR" exec dev zsh
