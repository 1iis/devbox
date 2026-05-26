# devbox

> [!WARNING]
> **`devbox` is beta workstation infrastructure.** It modifies host users, files, packages, Docker configuration, shell setup, Git setup, and optional systemd unit files.
>
> It is currently intended for our own small-team Ubuntu workstation workflow. Review the code first and test on a disposable VM or VPS before using it on an important machine.

`devbox` is a small, opinionated SWE workstation setup for an Ubuntu host and a disposable Docker container, with one `dev` work identity shared across both.

It is not a general platform. It is a practical workstation pattern:

- the host owns durable state, secrets, users, filesystems, SSH agent access, and Docker;
- the container is a rebuildable execution/tooling layer;
- the `dev` user exists on both host and container, with UID/GID `1111` by default;
- work files live on the host and are bind-mounted into the container;
- shell config, Git config, aliases, history, and daily tooling are kept close enough that `dev@box` and `dev@dev` feel like one working environment.

The goal is a small, good workstation: boring, explicit, rebuildable, and pleasant to use.

## Status

Current release: [**`v0.2.0-beta`**][release].

Supported beta/MVP workflow:

```text
admin user clones repo and bootstraps host
  -> host/sync.py creates/converges the dev user and runtime files
  -> dev user starts the container directly with Docker Compose
  -> dev works in either dev@box or dev@dev
```

The supported runtime path is **direct Docker Compose from an interactive `dev` login**.

The sync script can install and enable a systemd unit, but fully systemd-managed container startup with stable interactive SSH-agent semantics is deferred.

## What you get

- dedicated host work user: `dev`
- matching container user: `dev`
- shared UID/GID: `1111` by default
- shared work directories:
  - `/home/dev/git`
  - `/home/dev/pj`
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
host/sync.ipynb         literate development notebook/source
scripts/                small helper scripts
templates/              public-safe examples for local config
Makefile                daily command surface after bootstrap
```

**`host/sync.py`** is the important control-plane file. The scripts and Makefile are thin wrappers around the tested workflow. 

> [!TIP]
> See [**`host/sync.ipynb`**][sync-nb] at [Solveit][solveit] for the literate programming source.

## Quickstart

This is the supported beta/MVP bootstrap path.

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

## Daily use

From the host `dev` user:

```sh
cd ~/.devbox
./scripts/dev-in.sh
```

That is the normal “start and enter devbox” path.

The equivalent Makefile commands are:

```sh
cd ~/.devbox
make dcup      # start container
make shell     # enter dev@dev
make ps        # show service state
make logs      # follow logs
make dcdn      # stop container
```

The container is disposable. Your work is not: project files, shell config, Git config, SSH metadata, history, and selected tool state live on the host or in named Docker volumes.

## Manual bootstrap

The wrapper is intentionally small. The manual equivalent is useful when debugging `scripts/setup.sh` or developing `devbox` itself.

```sh
git clone https://github.com/1iis/devbox.git
cd devbox

python3 -m py_compile host/sync.py

python3 host/sync.py status \
  --name "Your Name" \
  --email you@example.com

sudo python3 host/sync.py enable \
  --name "Your Name" \
  --email you@example.com

sudo -iu dev
cd ~/.devbox
make dcup
make shell
```

To import existing keys during bootstrap:

```sh
python3 host/sync.py status \
  --name "Your Name" \
  --email you@example.com \
  --ssh-sign-key "$HOME/.ssh/sign" \
  --ssh-private-key "$HOME/.ssh/dev"
```

Then run the same command with `sudo ... enable`.

The key paths are bootstrap inputs. They are not part of the daily shell environment.

## Auth and persistence

GitHub CLI state is stored in the `gh-config` Docker named volume:

```sh
gh auth login
```

Codex state is stored in the `codex-config` Docker named volume:

```sh
codex
```

Both survive container rebuilds and recreation.

SSH auth and signing use host-owned key material. The container receives:

- the forwarded SSH agent socket;
- SSH config;
- known hosts;
- the public signing key.

Private keys should remain on the host.

## Local environment

`devbox` creates a local shell environment file if it is missing:

```text
/home/dev/.oh-my-zsh/custom/env.zsh
```

This file is create-once local state. `host/sync.py` creates it from `templates/env.zsh.example` if needed and does not overwrite existing content.

Use it for local shell environment variables or tool tokens if needed.

Do not use it as bootstrap configuration. Bootstrap inputs such as name, email, and SSH key paths should be passed to `scripts/setup.sh` or `host/sync.py`.

Do not commit real secrets.

## Runtime model

The supported beta/MVP runtime path is direct Docker Compose from an interactive `dev` login:

```sh
cd ~/.devbox
make dcup
make shell
```

The installed Compose runtime files live at:

```text
/home/dev/.config/dev-env
```

The active host-side repo/config copy lives at:

```text
/home/dev/.devbox
```

That directory is deliberately not bind-mounted into the container. Normal work should happen under bind-mounted work directories such as:

```text
/home/dev/git
/home/dev/pj
```

## Validation

Fast local checks:

```sh
make check
```

This currently checks:

- Python compilation for `host/sync.py`;
- `host/sync.py --help`;
- shell syntax for scripts;
- Docker Compose config parsing.

For fresh-host confidence, test on a disposable Ubuntu VM or VPS and run the full bootstrap path.

## Known caveats

- `devbox` is currently opinionated around Ubuntu hosts.
- The normal work user is always `dev`.
- UID/GID default to `1111`.
- Direct Docker Compose from an interactive `dev` login is the supported runtime path.
- The systemd unit can be installed/enabled, but full systemd-managed runtime with reliable interactive SSH-agent semantics is deferred.
- `host/sync.ipynb` is tracked as literate source/development context; `host/sync.py` is the runtime artifact.
- `devbox` is not a multi-user framework. Each installation gets its own `dev` identity.
- No container image is published yet.

## Not currently in scope

These may happen later, but are not part of the current MVP path:

- packaged `devbox` CLI;
- PyPI/`uvx` installation;
- published container images;
- generalized multi-user support;
- cloud-init-first workflow;
- full systemd-managed runtime;
- broad platform support beyond the current Ubuntu workflow.

## Design principles

- boring over clever
- explicit over magical
- host owns durable state
- container is disposable
- private keys stay out of the container
- local config is create-once where appropriate
- managed files are exact and reproducible
- daily workflow should be short and memorable

## License

MIT. See [`LICENSE`](./LICENSE).




[release]: https://github.com/1iis/devbox/releases/tag/v0.2.0-beta
[sync-nb]: https://share.solveit.pub/d/105311392cff6157618c3f412afb3c96
[solveit]: https://solve.it.com/

