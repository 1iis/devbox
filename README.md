> [!WARNING]
> **`devbox` is early alpha software. It modifies host users, files, packages, systemd units, Docker configuration, and shell/Git setup.**  
> Review the code first and test on a disposable Ubuntu VM or VPS before using it on an important machine.

---

# devbox

> A small SWE workstation setup built for a host machine and a Docker container, with one work identity shared across both.

The premise is basic: in isolation from your main/personal/admin user, `devbox` creates a dedicated `dev` user, and a corresponding `dev` user in a Docker container. Both `dev` users are in sync, including real-time shell history and configuration files. They both behave identically, as if one. This lets you run things either isolated in Docker or locally on the workstation seamlessly.

Global variables: used to install `devbox`. Change `NAME` and `EMAIL` to fit your `git` setup, in [`env.zsh`](/dotfiles/dev/.oh-my-zsh/custom/env.zsh_EDITME) renamed as such.

| `$var`  | Purpose | Example/Default
|-------|---------|-----------------
| `NAME`  | Full name | Your Name
| `EMAIL` | Git email | email@example.com
| `ID`    | UID and GID | `1111`
| `DEV`   | Name of `dev` user | `dev`
| `CTHOST`| Container hostname | `dev`

`devbox` gives you a boring, rebuildable, comfortable development environment:

- one host `dev` identity
- one container `dev` identity
- shared shell, Git, SSH, history, aliases, and work directories
- durable state on the host or in named volumes
- disposable container tooling
- no private keys baked into the container
- no magic beyond Docker, zsh, Git, and a small sync script

The goal is not maximal abstraction. The goal is a workstation you can understand, rebuild, and trust.

## Model

There are two layers:

```text
host
  owns users, files, secrets, SSH agent, Docker, durable work dirs

container
  owns tools, shell runtime, isolated agentic tooling, disposable execution state
```

The normal work identity is `dev`.

```text
dev@host       durable identity and source of truth
dev@container  clean execution layer with the same basic shape
```

The container should feel like the host `dev` user, but it should not become a second precious machine.

## Repository layout

```text
devbox/
  container/
    Dockerfile
    docker-compose.yml
    README.md

  dotfiles/
    dev/
      .zshrc
      .gitconfig
      .p10k.zsh
      .oh-my-zsh/
        custom/
          aliases.zsh
          dev.zsh
          history.zsh
          _docker.zsh
          _git.zsh
          _python.zsh
          10-rc.zsh
          dev/
            10-rc.zsh

  host/
    sync.py
    systemd/
      dev-container.service

  templates/
    env.zsh.example
    ssh_config.example
    gitconfig.example

  scripts/
    check.sh
    build-container.sh
    enter-container.sh
```

Each directory has one job:

| Path | Purpose |
|---|---|
| `container/` | Docker image and Compose service definition |
| `dotfiles/dev/` | Files installed into `/home/dev` |
| `host/` | Host setup sync and systemd integration |
| `templates/` | Public-safe examples for secrets and machine-local config |
| `scripts/` | Thin wrappers for common operations |

## What lives where

Durable work and identity live on the host:

```text
/home/dev/git
/home/dev/pj
/home/dev/.ssh
/home/dev/.gitconfig
/home/dev/.zshrc
/home/dev/.oh-my-zsh/custom
```

Container-only state lives in Docker volumes:

```text
gh-config      -> /home/dev/.config/gh
codex-config   -> /home/dev/.codex
```

Private keys stay on the host. The container uses the host SSH agent.

## Quickstart

Clone the repo:

```zsh
git clone https://github.com/1iis/devbox.git
cd devbox
```

On a fresh Ubuntu host, use Python for the first bootstrap step. `make` is installed by `host/sync.py`, so do not assume it exists yet:

```zsh
python3 -m py_compile host/sync.py
python3 host/sync.py status --name "Your Name" --email you@example.com
sudo python3 host/sync.py enable --name "Your Name" --email you@example.com
```

After that, the normal Makefile workflow is available. Host-state sync/status checks inspect `/home/dev` and system paths, so run them with `sudo` from the admin/installer user:

```zsh
make check
sudo make status
sudo make enable
```

For the MVP daily workflow, switch to the managed `dev` identity and start/enter the container from that login session. This preserves access to the interactive SSH agent via `SSH_AUTH_SOCK`:

```zsh
sudo -iu dev
cd ~/.config/dev-env
docker compose up -d
docker compose exec dev zsh
```

`make start` currently controls the systemd service path. That path is useful for validation and future polish, but the preferred MVP work loop is direct Compose from `dev`.

Prepare local config and secrets as needed:

```zsh
sudo -u dev cp templates/env.zsh.example /home/dev/.oh-my-zsh/custom/env.zsh
sudo -u dev editor /home/dev/.oh-my-zsh/custom/env.zsh
sudo -u dev editor /home/dev/.ssh/config
```

The sync command creates these files once if missing and will not overwrite local secret/config content afterwards.

## First-run authentication

Some tools authenticate once and persist their state in Docker volumes.

GitHub CLI:

```zsh
gh auth login
```

Codex CLI:

```zsh
codex
```

After first login, auth state survives container rebuilds.

## Daily use

Enter the container:

```zsh
dev
```

Rebuild the container:

```zsh
devub
```

Check status:

```zsh
devps
```

Stop it:

```zsh
devdown
```

The container is disposable. Your work is not.

## Shell layout

oh-my-zsh loads only top-level `*.zsh` files in `$ZSH_CUSTOM`.

This repo uses that deliberately:

```text
dotfiles/dev/.oh-my-zsh/custom/10-rc.zsh
```

is host-only `dev` setup.

```text
dotfiles/dev/.oh-my-zsh/custom/dev/10-rc.zsh
```

is container-only setup. Compose mounts it into the container as:

```text
/home/dev/.oh-my-zsh/custom/10-rc.zsh
```

So the host and container can share most files while keeping their startup behavior separate.

## Secrets

This repo should be safe to publish.

Do not commit:

- private SSH keys
- API keys
- `env.zsh`
- `.codex/`
- `.config/gh/`
- `.npm/`
- `.zsh_history`
- machine-local caches or logs

Public examples live in `templates/`.

Real secrets live on the machine or in a password manager.

## Design principles

- keep it small
- keep it explicit
- make rebuilds cheap
- keep secrets out of images
- mount durable data in
- bake container tools into the image
- let the host own identity
- let the container own disposable execution
- prefer boring tools over clever machinery

## Current stack

The container currently includes:

- Ubuntu 24.04
- zsh + oh-my-zsh
- powerlevel10k
- Git
- GitHub CLI
- uv
- Node.js LTS
- npm
- Codex CLI
- bubblewrap
- common terminal/dev tools

See `container/README.md` for container-specific details.

## Status

This repo is intentionally small and practical.

It is built for a tiny team that wants a reliable workstation pattern without adopting a full platform stack.
