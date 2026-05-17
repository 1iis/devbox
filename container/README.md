**Goal:** A disposable, reproducible Ubuntu 24.04 development environment running under Docker, usable as a daily driver work terminal.

**Desired properties:**
- Docker Compose-based: `docker compose up -d` starts it, `docker compose exec dev zsh` drops into a shell
- User `kit` with UID/GID matching host (1000), full sudo, `zsh` as default shell
- All tools pre-installed in the image (see `packages` in the build): `build-essential`, `git`, `curl`, `python-is-python3`, `btop`, `jq`, `yq`, `fzf`, `ripgrep`, `fd-find`, `bat`, `tldr`, `rclone`, `strace`, `tcpdump`, `uv`, `kitty-terminfo`, `node`, `npm`, `codex` CLI, and more.
- Oh-my-zsh + Powerlevel10k theme + zsh-autosuggestions + zsh-syntax-highlighting + fzf key bindings
- Bind mounts for: `~/.ssh`, `~/git`, `~/pj`, `~/.p10k.zsh`, `~/.config/gh`, `~/.codex`.
- Entrypoint handles: home directory ownership, …
- Unattended-upgrades configured (security-only, no reboot)

**Files:** `/container/Dockerfile`, `/container/docker-compose.yml`
