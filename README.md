> [!WARNING]
> **`devbox` is beta workstation infrastructure.** It modifies host users, files, packages, Docker configuration, systemd units, and shell/Git setup.
>
> It is currently intended for our own small-team Ubuntu workstation workflow. Review the code first and test on a disposable VM or VPS before using it on an important machine.

# devbox

A small, opinionated SWE workstation setup for an Ubuntu host and a disposable Docker container, with one `dev` work identity shared across both.

`devbox` is not a general platform. It is a practical workstation pattern:

- the host owns durable state, secrets, users, filesystems, SSH agent access, and Docker;
- the container is a rebuildable execution/tooling layer;
- the `dev` user exists on both host and container, with UID/GID `1111` by default;
- work files live on the host and are bind-mounted into the container;
- shell config, Git config, aliases, history, and daily tooling are kept close enough that `dev@box` and `dev@dev` feel like one working environment.

The point is a small, good workstation: boring, explicit, rebuildable, and pleasant to use.

## Status

Current release target: `v0.1.0-beta`.

Supported beta workflow:

```text
admin user clones repo and bootstraps host
  -> host/sync.py creates/converges the dev user and runtime files
  -> dev user starts the container directly with Docker Compose
  -> dev works in either dev@box or dev@dev
```

Direct Compose from an interactive `dev` login is the supported beta runtime path. The systemd unit can be installed/enabled by the sync script, but fully systemd-managed container startup with interactive SSH-agent semantics is deferred.

## What you get

- dedicated host work user: `dev`
- matching container user: `dev`
- shared work directories: `/home/dev/git` and `/home/dev/pj`
- Zsh, Oh My Zsh, Powerlevel10k, aliases, and history setup
- Git and GitHub CLI configuration
- SSH authentication/signing through host-owned key material and agent forwarding
- Docker Compose runtime under `/home/dev/.config/dev-env`
- active host-side repo/config copy at `/home/dev/.devbox`
- persistent Docker named volumes for GitHub CLI and Codex state
- disposable container rebuild/recovery workflow

Private keys are not baked into the image and should not be copied into the container. The container uses the host SSH agent and selected mounted public/config files.

## Repository layout

```text
container/              Dockerfile, Compose file, container docs
dotfiles/dev/           files installed into /home/dev
host/sync.py            host convergence engine
host/sync.ipynb         literate development notebook, not required at runtime
scripts/                small helper scripts
templates/              public-safe examples for local config
Makefile                daily command surface after bootstrap
```

`host/sync.py` is the important control-plane file. The scripts and Makefile are thin wrappers around the tested workflow.

## Quickstart

On a fresh-ish Ubuntu host, clone the repo as the existing admin/user account:

```sh
git clone https://github.com/1iis/devbox.git
cd devbox
chmod +x scripts/setup.sh scripts/dev-in.sh
./scripts/setup.sh
```

The setup script asks for:

- Git display name;
- Git email;
- optional existing SSH signing private key;
- optional existing SSH auth private key.

If key paths are omitted or do not exist, `host/sync.py` can generate fresh keys for the `dev` user.

After setup completes:

```sh
sudo -iu dev
cd ~/.devbox
./scripts/dev-in.sh
```

That starts the Compose runtime if needed and enters the container shell.

## Manual bootstrap

The wrapper is intentionally small. The manual equivalent is:

```sh
git clone https://github.com/1iis/devbox.git
cd devbox
python3 -m py_compile host/sync.py
python3 host/sync.py status --name "Your Name" --email you@example.com
sudo python3 host/sync.py enable --name "Your Name" --email you@example.com
sudo -iu dev
cd ~/.devbox
make dcup
make shell
```

To import existing keys:

```sh
python3 host/sync.py status \
  --name "Your Name" \
  --email you@example.com \
  --ssh-sign-key "$HOME/.ssh/sign" \
  --ssh-private-key "$HOME/.ssh/dev"
```

Then run the same command with `sudo ... enable`.

## Daily use

From the host `dev` user:

```sh
cd ~/.devbox
make dcup      # start container
make shell     # enter dev@dev
make ps        # show service state
make logs      # follow logs
make dcdn      # stop container
```

The helper script does the common start-and-enter path:

```sh
~/.devbox/scripts/dev-in.sh
```

The container is disposable. Your work is not: project files, shell config, Git config, SSH metadata, and history live on the host or in named Docker volumes.

## Auth and persistence

GitHub CLI state is stored in the `gh-config` Docker volume:

```sh
gh auth login
```

Codex state is stored in the `codex-config` Docker volume:

```sh
codex
```

Both survive container rebuilds and recreation.

SSH auth and signing use host-owned key material. Compose forwards the SSH agent socket into the container as `/ssh-agent` and sets:

```text
SSH_AUTH_SOCK=/ssh-agent
```

This works in the supported beta path because the container is started from an interactive `dev` login session.

## Updating and recovery

From `dev@box`:

```sh
cd ~/.devbox
git pull
make check
sudo make enable
make dcup
make shell
```

Rebuild the container when needed:

```sh
cd ~/.devbox
make build
make dcdn
make dcup
make shell
```

The image and container can be replaced; durable state should remain on the host or in named volumes.

## Local config and templates

Public examples live in `templates/`.

Local machine config is created once and should not be committed:

- `/home/dev/.oh-my-zsh/custom/env.zsh`
- `/home/dev/.ssh/config`
- `/home/dev/.zsh_history`
- Docker auth/config volumes
- Codex config

The sync script creates local files if missing and avoids overwriting secret/local state afterwards.

## Validation

Fast local checks:

```sh
make check
```

This currently checks:

- Python compile for `host/sync.py`;
- sync help output;
- shell script syntax;
- Docker Compose config parsing.

## Design principles

- keep it small;
- keep it boring;
- make changes reversible;
- host owns durable state;
- container is disposable;
- no private keys in the image;
- mount data instead of duplicating it;
- prefer direct standard tools over clever abstraction;
- excellent daily UX beats theoretical purity.

## Known limitations

- This is beta software for an opinionated small-team workflow.
- It is tested primarily on fresh Ubuntu hosts/VMs.
- Direct Compose from logged-in `dev` is the supported runtime path.
- Full systemd-managed startup with interactive SSH-agent behavior is deferred.
- Command names and helper scripts may change before a stable release.
- There is no packaged `devbox` CLI yet.
- No container image is published; build locally from this repo.

## License

MIT. See [`LICENSE`](./LICENSE).