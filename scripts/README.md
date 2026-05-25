# `scripts/``scripts/`

This directory contains small helper scripts around the `devbox` workstation setup.

The important distinction is:

- `host/sync.py` is the real reconciliation engine.
- `Makefile` is the normal command surface once the host has been bootstrapped.
- `scripts/` contains thin wrappers for common workflows and test/development convenience.

None of these scripts should grow into a second orchestration system. If a script starts accumulating real desired-state logic, that logic probably belongs in `host/sync.py`.

## Existing scripts

### `check.sh``check.sh`

Fast local validation.

It runs the cheap checks that should pass before committing or testing on a real host:

- compile `host/sync.py`;
- verify `host/sync.py --help`;
- syntax-check shell scripts with `bash -n`;
- validate the Docker Compose file with `docker compose config`.

This is what `make check` calls.

Equivalent manual flow:

```sh
python3 -m py_compile host/sync.py
python3 host/sync.py --help >/dev/null
bash -n scripts/*.sh
SSH_AUTH_SOCK="${SSH_AUTH_SOCK:-/tmp/devbox-ci-ssh-agent.sock}" \
  docker compose -f container/docker-compose.yml --project-directory container config >/dev/null
```

### `build-container.sh``build-container.sh`

Build the container image from the repo-local Compose file.

It is a small wrapper around:

```sh
docker compose -f container/docker-compose.yml --project-directory container build
```

Use this when testing the image from the repository checkout, before or independently of the installed runtime copy under `/home/dev/.config/dev-env`.

### `enter-container.sh``enter-container.sh`

Enter the running installed container shell.

It expects the installed runtime directory to exist, by default:

```text
/home/dev/.config/dev-env
```

and runs:

```sh
docker compose -f "$RUN_DIR/docker-compose.yml" --project-directory "$RUN_DIR" exec dev zsh
```

`DEVBOX_RUN_DIR` can override the runtime directory.

This is essentially the script form of `make shell`.

---

# Bootstrap convenience scripts

The two newer scripts, `setup.sh` and `dev-in.sh`, are deliberately more user-facing.

They exist because repeatedly testing a fresh install involves the same manual sequence:

1. clone repo;
2. provide name/email;
3. provide or generate SSH keys;
4. compile `host/sync.py`;
5. run status;
6. confirm enable;
7. switch to `dev`;
8. start and enter the container.

These scripts make that path fast without changing the underlying architecture.

They are not the product API yet. They are a convenience layer for dogfooding and beta-MVP testing.

## `setup.sh``setup.sh`

`setup.sh` is the admin-side bootstrap helper.

It is intended to be run from a freshly cloned repo by the installer/admin user, for example:

```sh
git clone https://github.com/1iis/devbox.git
cd devbox
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Depending on the exact version, it may call `sudo` internally for the parts that need root privileges, or it may be run with `sudo`. The important idea is that it automates the same sequence that can be performed manually.

## What `setup.sh` does`setup.sh` does

At a high level:

```text
admin user
    ↓
collect identity and key paths
    ↓
write dev env file
    ↓
compile sync.py
    ↓
ensure make exists
    ↓
run status
    ↓
ask for confirmation
    ↓
run enable
    ↓
tell user how to enter dev workflow
```

In more concrete terms, it performs the following steps.

### 1. Locate the repo root

The script begins by moving to the repository root, usually by resolving its own path.

Conceptually:

```sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
```

This matters because all following paths are repo-relative:

- `host/sync.py`;
- `templates/env.zsh.example`;
- `dotfiles/dev/.oh-my-zsh/custom/env.zsh`;
- `Makefile`.

The script should not depend on the caller’s current directory once it has started.

### 2. Collect identity values

The setup needs a Git identity for the managed `dev` user:

```text
NAME
EMAIL
```

These eventually become:

```ini
[user]
    name = ...
    email = ...
```

inside `/home/dev/.gitconfig`.

The script tries to make this convenient:

- if `NAME` or `EMAIL` already exist in the environment, use them;
- otherwise prompt interactively;
- do not continue until both are known.

Manual equivalent:

```sh
export NAME="Your Name"
export EMAIL="you@example.com"
```

or pass flags directly to `host/sync.py`:

```sh
python3 host/sync.py status --name "Your Name" --email you@example.com
```

### 3. Collect SSH key paths

The setup also needs to know what to do about two key pairs:

```text
sign / sign.pub
dev  / dev.pub
```

The intended target locations are:

```text
/home/dev/.ssh/sign
/home/dev/.ssh/sign.pub
/home/dev/.ssh/dev
/home/dev/.ssh/dev.pub
```

The signing key is used for SSH commit signing. The `dev` key is the ordinary SSH auth key for the `dev@box` identity.

The script asks for paths such as:

```text
SSH_SIGN_KEY=/home/onei/.ssh/sign
SSH_PRIVATE_KEY=/home/onei/.ssh/dev
```

If the paths exist, `host/sync.py enable` can import them into `/home/dev/.ssh`.

If they are omitted, the sync script may generate fresh keys, depending on the chosen flags and interactive answers.

Manual equivalent:

```sh
python3 host/sync.py status \
  --name "Your Name" \
  --email you@example.com \
  --ssh-sign-key /home/onei/.ssh/sign \
  --ssh-private-key /home/onei/.ssh/dev
```

### 4. Write `env.zsh``env.zsh`

The script creates the local environment file for the future `dev` shell:

```text
dotfiles/dev/.oh-my-zsh/custom/env.zsh
```

from the example/template file.

This file is intentionally not a generic public config file. It is local machine state. It may contain personal paths, email addresses, API keys, and other environment variables.

The important values are:

```sh
export NAME="..."
export EMAIL="..."
export SSH_SIGN_KEY="..."
export SSH_PRIVATE_KEY="..."
```

Manual equivalent:

```sh
cp templates/env.zsh.example dotfiles/dev/.oh-my-zsh/custom/env.zsh
nano dotfiles/dev/.oh-my-zsh/custom/env.zsh
```

This is useful because `enable` later copies this file into:

```text
/home/dev/.oh-my-zsh/custom/env.zsh
```

as a create-once local file.

### 5. Compile `host/sync.py``host/sync.py`

Before mutating the host, the script checks that the Python file at least compiles:

```sh
python3 -m py_compile host/sync.py
```

This is a cheap guard against syntax errors.

It is not a full test. It merely answers:

> Can Python parse this file?

That is still valuable on a fresh host because it catches broken exports or accidental edits before any privileged setup happens.

### 6. Ensure `make` exists`make` exists

A fresh Ubuntu host may not have `make`.

The normal workflow after bootstrap uses `make`, but the bootstrap itself cannot rely on it. Therefore `setup.sh` may install `make` early:

```sh
sudo apt-get update
sudo apt-get install -y make
```

This is a convenience only. `host/sync.py enable` also manages packages and should ensure `make` exists as part of the desired host state.

Installing it early simply lets the rest of the flow use Makefile targets sooner.

### 7. Run status

The script runs a dry-run first:

```sh
python3 host/sync.py status ...
```

This reports what would change without mutating the host.

On a fresh host, expected output includes many `would_change` entries:

- install packages;
- create `dev` group;
- create `dev` user;
- create directories;
- install dotfiles;
- render `.gitconfig`;
- create local config files;
- install the systemd unit;
- copy the repo to `/home/dev/.devbox` or equivalent;
- create/import SSH keys.

The point is to show the user the plan before applying it.

The state model is:

```text
status = inspect + report
enable = inspect + mutate + report
```

The same operation plan is used in both cases; only `apply` changes.

### 8. Ask for confirmation

After showing the dry-run, the script asks whether to continue.

This is intentionally boring and explicit. The next step will create users, install packages, write files under `/home/dev`, and touch systemd state.

A good setup script should pause before doing that.

### 9. Run enable

If confirmed, the script runs:

```sh
sudo python3 host/sync.py enable ...
```

This converges the host toward the desired `devbox` state.

After success, the important resulting state is:

```text
/home/dev/
├── .devbox/                     # copied repo/config checkout
├── .config/dev-env/             # installed Docker runtime files
├── .oh-my-zsh/                  # OMZ + custom files
├── .ssh/
│   ├── sign
│   ├── sign.pub
│   ├── dev
│   └── dev.pub
├── .gitconfig
├── .p10k.zsh
└── .zshrc
```

The exact tree may evolve, but the conceptual split should remain:

```text
~/.devbox              active repo/config checkout
~/.config/dev-env      installed container runtime
~/.ssh                 dev identity material
~/.oh-my-zsh/custom    shell fragments and local env
```

### 10. Hand off to `dev``dev`

At the end, the script should not pretend that installation is the same thing as daily use.

The next step is to enter the managed work identity:

```sh
sudo -iu dev
```

From there, the user can run the `dev`-side helper:

```sh
~/.devbox/scripts/dev-in.sh
```

or manually:

```sh
cd ~/.devbox
make dcup
make shell
```

A friendly final message from `setup.sh` should therefore say something like:

```text
Installed.

Next:
  sudo -iu dev

Then:
  cd ~/.devbox
  scripts/dev-in.sh
```

## Why `setup.sh` is not the real engine`setup.sh` is not the real engine

`setup.sh` is glue.

It should not decide desired state. It should not know how to create users, install dotfiles, repair metadata, write systemd units, or validate Compose.

Those jobs belong to `host/sync.py`.

The script exists to reduce this:

```sh
python3 -m py_compile host/sync.py
python3 host/sync.py status --name ... --email ... --ssh-sign-key ... --ssh-private-key ...
sudo python3 host/sync.py enable --name ... --email ... --ssh-sign-key ... --ssh-private-key ...
sudo -iu dev
cd ~/.devbox
make dcup
make shell
```

to a guided, repeatable flow.

That makes it valuable for testing and dogfooding even if a future CLI eventually replaces it.

---

## `dev-in.sh``dev-in.sh`

`dev-in.sh` is the `dev`-side entry helper.

It is intended to be run after:

```sh
sudo -iu dev
```

At that point the user is no longer the admin installer. They are the managed work user, with the intended shell, Git config, SSH config, Docker group membership, and runtime files.

The script then does the daily entry sequence:

```text
dev@box
    ↓
cd ~/.devbox
    ↓
make dcup
    ↓
make shell
    ↓
dev@dev
```

## What `dev-in.sh` does`dev-in.sh` does

The core behavior is intentionally tiny:

```sh
cd ~/.devbox
make dcup
make shell
```

That means:

1. enter the active devbox repo/config checkout;
2. start the Compose stack from the installed runtime directory;
3. enter the container shell.

The Makefile hides the exact Compose path:

```text
/home/dev/.config/dev-env/docker-compose.yml
```

so the user does not need to remember it.

### Step 1: `cd ~/.devbox``cd ~/.devbox`

The active installation repo lives at:

```text
/home/dev/.devbox
```

This is deliberately outside bind-mounted container work directories.

The container should not be able to casually edit the active host-side installation logic. That preserves a small but important isolation boundary:

```text
host devbox config controls container
container should not control host devbox config
```

This is why `~/.devbox` is preferable to putting the active checkout under a path that is routinely mounted into the container.

### Step 2: `make dcup``make dcup`

`make dcup` starts the installed Compose runtime:

```sh
docker compose \
  -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env \
  up -d
```

If the image does not exist yet, Docker Compose may build it automatically depending on the current Compose behavior and local state.

This is the supported MVP runtime path because it runs from an interactive `dev` login session. That means `SSH_AUTH_SOCK` is available, so the SSH-agent bind mount works.

This is intentionally different from the current systemd path. The systemd unit is installed and useful for later polish, but it does not yet solve the interactive SSH-agent socket problem.

### Step 3: `make shell``make shell`

`make shell` enters the running container:

```sh
docker compose \
  -f /home/dev/.config/dev-env/docker-compose.yml \
  --project-directory /home/dev/.config/dev-env \
  exec dev zsh
```

After this, the user is in:

```text
dev@dev
```

with the container shell and tools.

The container is meant to be disposable. The durable state lives outside it:

```text
host bind mounts       project/work files and selected config
named Docker volumes   tool auth/state such as gh and codex
host SSH agent         private key access
```

### Manual equivalent

Everything `dev-in.sh` does can be reproduced manually:

```sh
sudo -iu dev
cd ~/.devbox
make dcup
make shell
```

or even more explicitly:

```sh
sudo -iu dev
cd ~/.config/dev-env
docker compose up -d
docker compose exec dev zsh
```

The `~/.devbox` + `make` route is preferred because it keeps the user at the repo command surface rather than the installed runtime internals.

## Intended use

Typical first run after `setup.sh`:

```sh
sudo -iu dev
cd ~/.devbox
scripts/dev-in.sh
```

Typical later run:

```sh
sudo -iu dev
~/.devbox/scripts/dev-in.sh
```

or, if `scripts/` is on the path later:

```sh
dev-in.sh
```

## Design boundary

`dev-in.sh` should stay small.

It should not authenticate GitHub. It should not log into Codex. It should not repair host files. It should not run privileged sync. It should not edit dotfiles.

Those are separate concerns:

```text
host convergence     host/sync.py
admin bootstrap      setup.sh
daily entry          dev-in.sh
GitHub auth          gh auth login
Codex auth           codex login
container rebuild    make build / make dcup
```

The virtue of the script is that it is obvious. If it ever stops being obvious, it should probably be deleted or replaced by a real CLI subcommand.

---

# Current workflow summary

A complete test install looks like:

```sh
git clone https://github.com/1iis/devbox.git
cd devbox
chmod +x scripts/setup.sh
scripts/setup.sh
```

Then:

```sh
sudo -iu dev
cd ~/.devbox
scripts/dev-in.sh
```

The manual equivalent is:

```sh
git clone https://github.com/1iis/devbox.git
cd devbox

python3 -m py_compile host/sync.py

python3 host/sync.py status \
  --name "Your Name" \
  --email you@example.com \
  --ssh-sign-key "$HOME/.ssh/sign" \
  --ssh-private-key "$HOME/.ssh/dev"

sudo python3 host/sync.py enable \
  --name "Your Name" \
  --email you@example.com \
  --ssh-sign-key "$HOME/.ssh/sign" \
  --ssh-private-key "$HOME/.ssh/dev"

sudo -iu dev
cd ~/.devbox
make dcup
make shell
```

That is all the scripts are doing.

They are not magic. They are memory.
