#!/usr/bin/env bash
set -euo pipefail

DEVDIR="${DEVDIR:-$HOME/.devbox}"

cd "$DEVDIR"
make dcup && make ps && make shell
