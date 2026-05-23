# devbox container

A disposable, reproducible Ubuntu 24.04 development container for the `devbox` workstation pattern.

The container is not the source of truth for important state. It is a clean execution and tooling layer on top of the host `dev` user's files, configuration, SSH agent, and Docker daemon.

## Model

The container runs as:

```text
user: dev
uid: 1111 by default
gid: 1111 by default
hostname: dev
home: /home/dev
```

The intended host/container pairing is:

```text
dev@box  -> durable host work identity
dev@dev  -> disposable container work shell
```

The host owns durable state. The container consumes selected host files through bind mounts and named Docker volumes.

## Files

```text
container/Dockerfile
container/docker-compose.yml
```

Installed runtime location on the host:

```text
/home/dev/.config/dev-env
```

Typical usage from that directory:

```bash
docker compose up -d
docker compose exec dev zsh
```

Or, once the host aliases/systemd integration are installed, use the higher-level `devbox`/shell helpers from the host environment.

## Dockerfile

The image is based on:

```text
ubuntu:24.04
```

It creates a `dev` user and group using build args:

```text
UID=1111
GID=1111
```

The image installs a daily-driver command-line toolkit, including:

- build tools
- Git
- GitHub CLI
- zsh
- oh-my-zsh
- Powerlevel10k
- zsh-autosuggestions
- zsh-syntax-highlighting
- fzf
- ripgrep
- fd-find
- bat
- tree
- jq / yq
- btop / htop
- rclone
- strace
- tcpdump
- Docker CLI
- uv
- Node.js under `/opt/node`
- npm global prefix under `/home/dev/.npm/global`
- OpenAI Codex CLI
- bubblewrap for sandbox support

The container command is intentionally simple:

```text
sleep infinity
```

There is no SSH server and no special entrypoint ownership logic. The container is entered with Docker Compose, for example:

```bash
docker compose exec dev zsh
```

## Compose service

The Compose service is named:

```text
dev
```

It sets:

```text
container_name: dev
hostname: dev
working_dir: /home/dev
user: ${UID:-1111}:${GID:-1111}
SSH_AUTH_SOCK=/ssh-agent
```

The host SSH agent socket is forwarded into the container. Private SSH keys are not copied into the image and are not bind-mounted into the container.

## Mounted host state

The container bind-mounts selected host paths from `/home/dev`.

Work directories:

```text
/home/dev/git -> /home/dev/git
/home/dev/pj  -> /home/dev/pj
```

Shell and prompt configuration:

```text
/home/dev/.zshrc
/home/dev/.p10k.zsh
/home/dev/.zsh_history
/home/dev/.oh-my-zsh/custom/aliases.zsh
/home/dev/.oh-my-zsh/custom/dev.zsh
/home/dev/.oh-my-zsh/custom/_git.zsh
/home/dev/.oh-my-zsh/custom/_python.zsh
/home/dev/.oh-my-zsh/custom/history.zsh
/home/dev/.oh-my-zsh/custom/env.zsh
```

Container-specific shell setup:

```text
/home/dev/.oh-my-zsh/custom/dev/10-rc.zsh
  -> /home/dev/.oh-my-zsh/custom/10-rc.zsh inside the container
```

This works because oh-my-zsh loads top-level `.zsh` files from `$ZSH_CUSTOM`, but does not auto-load files from subdirectories.

SSH metadata and signing public key:

```text
/home/dev/.ssh/config
/home/dev/.ssh/known_hosts
/home/dev/.ssh/sign.pub
```

Git configuration:

```text
/home/dev/.gitconfig
```

The private key material remains host-only. SSH authentication and SSH commit signing use the forwarded SSH agent and mounted public/config metadata.

## Named volumes

Tool authentication/state that should survive container rebuilds is stored in Docker named volumes:

```text
gh-config     -> /home/dev/.config/gh
codex-config  -> /home/dev/.codex
```

This keeps container rebuilds cheap while avoiding unnecessary host-path coupling for tool-specific state.

## Host Docker access

The Compose file includes a commented Docker socket mount:

```yaml
# - /var/run/docker.sock:/var/run/docker.sock
```

Leave this disabled unless the container genuinely needs to control the host Docker daemon. Mounting the Docker socket gives the container broad control over the host.

## Rebuild philosophy

The container should be safe to discard and recreate.

Durable data belongs on the host or in explicit named volumes. If the container gets stale or messy, rebuild it rather than preserving it by hand.

Useful commands from `/home/dev/.config/dev-env`:

```bash
docker compose build
docker compose up -d
docker compose exec dev zsh
docker compose down
```
