# devbox container

Disposable Ubuntu 24.04 development container for the `devbox` workstation pattern.

The container is the rebuildable execution layer. Durable state, work files, Git identity, SSH agent access, and local shell configuration live on the host under `/home/dev` and are bind-mounted into the container.

## Model

- host user: `dev`, UID/GID `1111` by default
- container user: `dev`, UID/GID passed through from Compose, defaulting to `1111`
- container hostname: `dev`
- service/container name: `dev`
- runtime directory on host: `/home/dev/.config/dev-env`

Start the container with Docker Compose:

```bash
docker compose up -d
```

Enter the shell:

```bash
docker compose exec dev zsh
```

The container command is intentionally simple:

```bash
sleep infinity
```

There is no SSH daemon, no entrypoint ownership repair script, and no private state that should make the container precious.

## Image contents

The image is based on `ubuntu:24.04` and installs a normal command-line SWE toolkit, including:

- build tools, Git, curl, sudo, zsh, nano
- Python via `python-is-python3`
- GitHub CLI, Docker CLI, uv
- fzf, ripgrep, fd-find, bat, tree, jq, yq, tldr
- btop, htop, rclone, strace, netcat, tcpdump, acl
- kitty terminfo
- bubblewrap for Codex sandboxing
- Node.js under `/opt/node`
- npm global prefix at `/home/dev/.npm/global`
- `@openai/codex` installed globally
- oh-my-zsh, Powerlevel10k, zsh-autosuggestions, and zsh-syntax-highlighting

Runtime Node/npm PATH setup is handled by the container-only zsh fragment mounted as:

```text
/home/dev/.oh-my-zsh/custom/10-rc.zsh
```

## Mounted host state

Compose bind-mounts host-owned work state into the container, including:

- `/home/dev/git` → `/home/dev/git`
- `/home/dev/pj` → `/home/dev/pj`
- `/home/dev/.zshrc`
- selected files from `/home/dev/.oh-my-zsh/custom/`
- `/home/dev/.p10k.zsh`
- `/home/dev/.gitconfig`
- `/home/dev/.zsh_history`
- `/home/dev/.oh-my-zsh/custom/env.zsh`

The intent is that `dev@box` and `dev@dev` share the same practical shell and Git behavior without turning the container into a second source of truth.

## SSH and signing

Private SSH keys stay on the host.

The container receives only:

- the forwarded host SSH agent socket at `/ssh-agent`
- `/home/dev/.ssh/config`
- `/home/dev/.ssh/known_hosts`
- `/home/dev/.ssh/sign.pub`

Compose sets:

```text
SSH_AUTH_SOCK=/ssh-agent
```

This allows GitHub SSH auth, server SSH auth, and SSH commit signing to work through host-owned identity material without copying private keys into the container.

## Persisted tool auth/state

Some tool state is intentionally persisted in Docker named volumes:

- `gh-config` mounted at `/home/dev/.config/gh`
- `codex-config` mounted at `/home/dev/.codex`

This lets GitHub CLI and Codex authentication survive container rebuilds while keeping the container itself disposable.

## Host Docker access

The Compose file includes a commented Docker socket mount:

```yaml
# - /var/run/docker.sock:/var/run/docker.sock
```

Enable this only deliberately. Mounting the host Docker socket gives the container broad control over the host Docker daemon.

## Files

- `Dockerfile` defines the image.
- `docker-compose.yml` defines the local runtime shape.

In an installed host setup, these files are copied to:

```text
/home/dev/.config/dev-env/
```
