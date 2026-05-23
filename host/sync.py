from pathlib import Path
import argparse, grp, os, pwd, shutil, subprocess, sys, tempfile
from string import Template

ROOT = Path(__file__).resolve().parents[1]
DEV = "dev"
ID = 1111
CTHOST = "dev"
HOME = Path("/home/dev")
RUN = HOME/".config/dev-env"
APP = "dev-container.service"
PKGS = [
    "ca-certificates", "curl", "git", "gh", "make", "zsh", "openssh-client", "sudo",
    "docker.io", "docker-compose-v2", "python3", "fzf", "ripgrep", "fd-find",
    "bat", "tree",
]

CMDS = [
    "curl", "git", "gh", "make", "zsh", "ssh", "sudo", "docker", "python3",
    "fzf", "rg", "fdfind", "batcat", "tree",
]
DIRS = [
    {"path": HOME/"git", "owner": "dev:dev", "mode": 0o755},
    {"path": HOME/"pj", "owner": "dev:dev", "mode": 0o755},
    {"path": HOME/".config", "owner": "dev:dev", "mode": 0o755},
    {"path": RUN, "owner": "dev:dev", "mode": 0o755},
    {"path": HOME/".oh-my-zsh", "owner": "dev:dev", "mode": 0o755},
    {"path": HOME/".oh-my-zsh/custom", "owner": "dev:dev", "mode": 0o755},
    {"path": HOME/".oh-my-zsh/custom/dev", "owner": "dev:dev", "mode": 0o755},
    {"path": HOME/".ssh", "owner": "dev:dev", "mode": 0o700},
]
FILES = [
    {"src": ROOT/"dotfiles/dev/.zshrc", "dst": HOME/".zshrc", "owner": "dev:dev", "mode": 0o644},
    {"src": ROOT/"dotfiles/dev/.p10k.zsh", "dst": HOME/".p10k.zsh", "owner": "dev:dev", "mode": 0o644},
    {"src": ROOT/"container/Dockerfile", "dst": RUN/"Dockerfile", "owner": "dev:dev", "mode": 0o644},
    {"src": ROOT/"container/docker-compose.yml", "dst": RUN/"docker-compose.yml", "owner": "dev:dev", "mode": 0o644},
    {"src": ROOT/"container/README.md", "dst": RUN/"README.md", "owner": "dev:dev", "mode": 0o644},
]

ZSH_FILES = [
    "10-rc.zsh", "aliases.zsh", "dev.zsh", "history.zsh",
    "_docker.zsh", "_git.zsh", "_python.zsh", "i.zsh",
    "dev/10-rc.zsh",
]

RENDER = [
    {"src": ROOT/"dotfiles/dev/.gitconfig", "dst": HOME/".gitconfig", "owner": "dev:dev", "mode": 0o644},
]

ONCE = [
    {"src": ROOT/"templates/env.zsh.example", "dst": HOME/".oh-my-zsh/custom/env.zsh", "owner": "dev:dev", "mode": 0o600},
    {"src": ROOT/"templates/ssh_config.example", "dst": HOME/".ssh/config", "owner": "dev:dev", "mode": 0o600},
    {"src": None, "dst": HOME/".zsh_history", "owner": "dev:dev", "mode": 0o600, "content": ""},
]
def cli(argv=None) -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        prog="devbox sync",
        description="Check or converge the devbox host workstation state.",
    )
    p.add_argument(
        "cmd", nargs="?", default="status",
        choices=["status", "enable", "start", "restart"],
        help="sync action; default: status",
    )
    p.add_argument("--name", help="Git/user display name for rendered config")
    p.add_argument("--email", help="Git/user email for rendered config")
    p.add_argument("--dev", default=os.environ.get("DEV", DEV), help=f"work user name; default: {DEV}")
    p.add_argument("--id", type=int, default=int(os.environ.get("ID", ID)), help=f"UID/GID; default: {ID}")
    p.add_argument("--cthost", default=os.environ.get("CTHOST", CTHOST), help=f"container hostname; default: {CTHOST}")
    p.add_argument("--root", type=Path, default=ROOT, help="repo root; default: inferred from this file")
    p.add_argument("-y", "--yes", action="store_true", help="assume yes for package/system mutations")
    p.add_argument("-v", "--verbose", action="store_true", help="print extra command details")
    return p.parse_args(argv)
def cfg(a: argparse.Namespace, env=os.environ) -> dict:
    """Build the effective sync configuration."""
    gu = git_user()
    name = a.name or env.get("NAME") or gu.get("name")
    email = a.email or env.get("EMAIL") or gu.get("email")

    if not name and sys.stdin.isatty():
        name = input("Name for Git config: ").strip() or None
    if not email and sys.stdin.isatty():
        email = input("Email for Git config: ").strip() or None
    if not name or not email:
        raise SystemExit("NAME and EMAIL are required: pass --name/--email, set env vars, or configure global git user.name/user.email")

    home = Path(f"/home/{a.dev}")
    return {
        "cmd": a.cmd,
        "apply": a.cmd != "status",
        "name": name,
        "email": email,
        "dev": a.dev,
        "id": a.id,
        "gid": a.id,
        "cthost": a.cthost,
        "home": home,
        "root": a.root,
        "run": home/".config/dev-env",
        "app": APP,
        "yes": a.yes,
        "verbose": a.verbose,
    }


def git_user() -> dict:
    """Return global Git user.name/user.email when available."""
    r = {}
    for key, out_key in [("user.name", "name"), ("user.email", "email")]:
        cp = cmd(["git", "config", "--global", key])
        if cp.returncode == 0 and cp.stdout.strip():
            r[out_key] = cp.stdout.strip()
    return r
def target(cmd: str) -> list[str]:
    """Return resource groups selected by a sync command."""
    return {
        "status":  ["host", "systemd", "validate"],
        "enable":  ["host", "systemd", "enable", "validate"],
        "start":   ["host", "systemd", "enable", "validate", "start"],
        "restart": ["host", "systemd", "enable", "validate", "restart"],
    }[cmd]
def plan(c: dict, groups: list[str]) -> list[dict]:
    """Build operation dictionaries for the selected resource groups."""
    ops = []
    home, root, run = c["home"], c["root"], c["run"]
    dev, id = c["dev"], c["id"]
    own = f"{dev}:{dev}"

    if "host" in groups:
        ops.append({"kind": "pkgs", "name": "apt packages", "pkgs": PKGS})
        ops += [{"kind": "cmd", "name": f"command {x}", "cmd": x} for x in CMDS]
        ops.append({"kind": "group", "name": f"group {dev}", "group": dev, "gid": id})
        ops.append({"kind": "user", "name": f"user {dev}", "user": dev, "uid": id, "gid": id, "home": home, "shell": "/usr/bin/zsh", "groups": ["sudo", "docker"]})

        dirs = [{**d, "path": Path(str(d["path"]).replace(str(HOME), str(home))), "owner": own} for d in DIRS]
        ops += [{"kind": "dir", "name": f"dir {d['path']}", **d} for d in dirs]

        files = [
            {"src": root/"dotfiles/dev/.zshrc", "dst": home/".zshrc", "owner": own, "mode": 0o644},
            {"src": root/"dotfiles/dev/.p10k.zsh", "dst": home/".p10k.zsh", "owner": own, "mode": 0o644},
            {"src": root/"container/Dockerfile", "dst": run/"Dockerfile", "owner": own, "mode": 0o644},
            {"src": root/"container/docker-compose.yml", "dst": run/"docker-compose.yml", "owner": own, "mode": 0o644},
            {"src": root/"container/README.md", "dst": run/"README.md", "owner": own, "mode": 0o644},
        ]
        zsrc = root/"dotfiles/dev/.oh-my-zsh/custom"
        zdst = home/".oh-my-zsh/custom"
        files += [{"src": zsrc/x, "dst": zdst/x, "owner": own, "mode": 0o644} for x in ZSH_FILES]
        ops += [{"kind": "file", "name": f"file {f['dst']}", **f} for f in files]

        renders = [{"src": root/"dotfiles/dev/.gitconfig", "dst": home/".gitconfig", "owner": own, "mode": 0o644}]
        ops += [{"kind": "render", "name": f"render {r['dst']}", **r} for r in renders]

        once = [
            {"src": root/"templates/env.zsh.example", "dst": home/".oh-my-zsh/custom/env.zsh", "owner": own, "mode": 0o600},
            {"src": root/"templates/ssh_config.example", "dst": home/".ssh/config", "owner": own, "mode": 0o600},
            {"src": None, "dst": home/".zsh_history", "owner": own, "mode": 0o600, "content": ""},
        ]
        ops += [{"kind": "once", "name": f"create-once {o['dst']}", **o} for o in once]

    if "systemd" in groups:
        ops.append({"kind": "unit", "name": f"unit {c['app']}", "path": Path("/etc/systemd/system")/c["app"]})
    if "enable" in groups:
        ops.append({"kind": "svc", "name": f"enable {c['app']}", "svc": c["app"], "state": "enabled"})
    if "validate" in groups:
        ops.append({"kind": "compose", "name": "docker compose config", "cwd": run})
    if "start" in groups:
        ops.append({"kind": "svc", "name": f"start {c['app']}", "svc": c["app"], "state": "started"})
    if "restart" in groups:
        ops.append({"kind": "svc", "name": f"restart {c['app']}", "svc": c["app"], "state": "restarted"})
    return ops
def res(name: str, state: str = "ok", detail: str = "") -> dict:
    """Return a standard operation result dictionary."""
    return {"name": name, "state": state, "detail": detail}


def chg(apply: bool) -> str:
    """Return the mutation state appropriate for apply/dry-run mode."""
    return "changed" if apply else "would_change"
def op(o: dict, c: dict, apply: bool) -> dict:
    """Run one operation by dispatching on o['kind']."""
    f = {
        "pkgs": ensure_pkgs,
        "cmd": ensure_cmd,
        "group": ensure_group,
        "user": ensure_user,
        "dir": ensure_dir,
        "file": ensure_file,
        "render": ensure_render,
        "once": ensure_once,
        "unit": ensure_unit,
        "svc": ensure_svc,
        "compose": check_compose,
    }.get(o.get("kind"))
    if not f:
        return res(o.get("name", "operation"), "error", f"unknown operation kind: {o.get('kind')}")
    return f(o, c, apply)
def run_ops(ops: list[dict], c: dict, apply: bool) -> list[dict]:
    """Run all operations and return result dictionaries."""
    rs = []
    for o in ops:
        try:
            rs.append(op(o, c, apply))
        except Exception as e:
            rs.append(res(o.get("name", "operation"), "error", f"{type(e).__name__}: {e}"))
    return rs
def ensure_pkgs(o: dict, c: dict, apply: bool) -> dict:
    """Ensure required apt packages are installed."""
    miss = apt_missing(o["pkgs"])
    if not miss:
        return res(o["name"])
    if not apply:
        return res(o["name"], "would_change", "install: " + " ".join(miss))
    return apt_install(miss)


def ensure_cmd(o: dict, c: dict, apply: bool) -> dict:
    """Ensure a command is available on PATH."""
    return res(o["name"]) if need(o["cmd"]) else res(o["name"], "warn", "missing from PATH")
def ensure_group(o: dict, c: dict, apply: bool) -> dict:
    """Ensure the dev group exists with the desired GID."""
    name, want = o["group"], o["gid"]
    try:
        g = grp.getgrnam(name)
        if g.gr_gid == want: return res(o["name"])
        return res(o["name"], "warn", f"exists with gid {g.gr_gid}, expected {want}")
    except KeyError:
        pass
    try:
        other = grp.getgrgid(want).gr_name
        return res(o["name"], "warn", f"gid {want} already used by group {other}")
    except KeyError:
        pass
    if not apply: return res(o["name"], "would_change", f"groupadd --gid {want} {name}")
    cp = cmd(["groupadd", "--gid", str(want), name])
    return res(o["name"], "changed" if cp.returncode == 0 else "error", cp.stderr.strip())


def ensure_user(o: dict, c: dict, apply: bool) -> dict:
    """Ensure the dev user exists with desired UID, group, home, shell, and memberships."""
    name, want = o["user"], o["uid"]
    groups = set(o.get("groups", []))
    try:
        u = pwd.getpwnam(name)
        details = []
        if u.pw_uid != want: details.append(f"uid {u.pw_uid} != {want}")
        if u.pw_gid != o["gid"]: details.append(f"gid {u.pw_gid} != {o['gid']}")
        if Path(u.pw_dir) != o["home"]: details.append(f"home {u.pw_dir} != {o['home']}")
        if u.pw_shell != o["shell"]: details.append(f"shell {u.pw_shell} != {o['shell']}")
        have = {g.gr_name for g in grp.getgrall() if name in g.gr_mem}
        missing = sorted(groups - have)
        if details: return res(o["name"], "warn", "; ".join(details))
        if not missing: return res(o["name"])
        if not apply: return res(o["name"], "would_change", "add groups: " + ",".join(missing))
        cp = cmd(["usermod", "-aG", ",".join(missing), name])
        return res(o["name"], "changed" if cp.returncode == 0 else "error", cp.stderr.strip())
    except KeyError:
        pass
    try:
        other = pwd.getpwuid(want).pw_name
        return res(o["name"], "warn", f"uid {want} already used by user {other}")
    except KeyError:
        pass
    xs = ["useradd", "--uid", str(want), "--gid", str(o["gid"]), "--create-home", "--home-dir", str(o["home"]), "--shell", o["shell"], "--groups", ",".join(o["groups"]), name]
    if not apply: return res(o["name"], "would_change", " ".join(xs))
    cp = cmd(xs)
    return res(o["name"], "changed" if cp.returncode == 0 else "error", cp.stderr.strip())
def ensure_dir(o: dict, c: dict, apply: bool) -> dict:
    """Ensure a directory exists with desired ownership and mode."""
    p = o["path"]
    if p.exists() and not p.is_dir():
        return res(o["name"], "error", "exists but is not a directory")
    ok = p.is_dir() and same_meta(p, o["owner"], o["mode"])
    if ok: return res(o["name"])
    if not apply: return res(o["name"], "would_change", "create/repair directory")
    p.mkdir(parents=True, exist_ok=True)
    u, g = ids(o["owner"])
    os.chown(p, u, g); os.chmod(p, o["mode"])
    return res(o["name"], "changed")
def ensure_file(o: dict, c: dict, apply: bool) -> dict:
    """Ensure an exact managed file matches source content, owner, and mode."""
    src, dst = o["src"], o["dst"]
    if not src.exists(): return res(o["name"], "error", f"missing source: {src}")
    b = src.read_bytes()
    ok = read(dst) == b and same_meta(dst, o["owner"], o["mode"])
    if ok: return res(o["name"])
    if not apply: return res(o["name"], "would_change", "copy/repair managed file")
    write(dst, b, o["mode"], o["owner"])
    return res(o["name"], "changed")
def ensure_render(o: dict, c: dict, apply: bool) -> dict:
    """Ensure a rendered managed file matches desired content, owner, and mode."""
    src, dst = o["src"], o["dst"]
    if not src.exists(): return res(o["name"], "error", f"missing source: {src}")
    b = render(src.read_text(), c).encode()
    ok = read(dst) == b and same_meta(dst, o["owner"], o["mode"])
    if ok: return res(o["name"])
    if not apply: return res(o["name"], "would_change", "render/repair managed file")
    write(dst, b, o["mode"], o["owner"])
    return res(o["name"], "changed")
def ensure_once(o: dict, c: dict, apply: bool) -> dict:
    """Create a local file only if missing; never overwrite existing content."""
    dst = o["dst"]
    if dst.exists():
        if same_meta(dst, o["owner"], o["mode"]): return res(o["name"])
        if not apply: return res(o["name"], "would_change", "repair metadata only")
        u, g = ids(o["owner"])
        os.chown(dst, u, g); os.chmod(dst, o["mode"])
        return res(o["name"], "changed", "metadata only")
    if o.get("src"):
        if not o["src"].exists(): return res(o["name"], "error", f"missing source: {o['src']}")
        b = o["src"].read_bytes()
    else:
        b = o.get("content", "").encode()
    if not apply: return res(o["name"], "would_change", "create local file")
    write(dst, b, o["mode"], o["owner"])
    return res(o["name"], "changed")
def ensure_unit(o: dict, c: dict, apply: bool) -> dict:
    """Ensure the managed systemd unit file exists and is current."""
    p = o["path"]
    b = unit_text(c).encode()
    ok = read(p) == b and p.exists()
    if ok: return res(o["name"])
    if not apply: return res(o["name"], "would_change", "install/repair unit; daemon-reload needed")
    write(p, b, 0o644, None)
    cp = cmd(["systemctl", "daemon-reload"])
    if cp.returncode != 0: return res(o["name"], "error", cp.stderr.strip())
    return res(o["name"], "changed", "daemon-reload")


def ensure_svc(o: dict, c: dict, apply: bool) -> dict:
    """Ensure requested systemd service action/state."""
    svc, state = o["svc"], o["state"]
    if state == "enabled":
        cp = cmd(["systemctl", "is-enabled", svc])
        if cp.returncode == 0: return res(o["name"])
        if not apply: return res(o["name"], "would_change", "systemctl enable")
        cp = cmd(["systemctl", "enable", svc])
    elif state == "started":
        cp = cmd(["systemctl", "is-active", svc])
        if cp.returncode == 0: return res(o["name"])
        if not apply: return res(o["name"], "would_change", "systemctl start")
        cp = cmd(["systemctl", "start", svc])
    elif state == "restarted":
        if not apply: return res(o["name"], "would_change", "systemctl restart")
        cp = cmd(["systemctl", "restart", svc])
    else:
        return res(o["name"], "error", f"unknown service state: {state}")
    return res(o["name"], "changed" if cp.returncode == 0 else "error", cp.stderr.strip())
def check_compose(o: dict, c: dict, apply: bool) -> dict:
    """Validate the installed Docker Compose configuration."""
    if not need("docker"):
        return res(o["name"], "warn", "docker command missing")
    yml = o["cwd"]/"docker-compose.yml"
    if not yml.exists():
        return res(o["name"], "warn", f"missing {yml}")
    env = os.environ.copy()
    env.setdefault("SSH_AUTH_SOCK", "/tmp/devbox-ci-ssh-agent.sock")
    cp = subprocess.run(["docker", "compose", "-f", str(yml), "--project-directory", str(o["cwd"]), "config"], env=env, text=True, capture_output=True)
    if cp.returncode != 0:
        return res(o["name"], "warn", cp.stderr.strip())
    return res(o["name"])
def cmd(xs: list[str], check: bool = False, input: str | None = None) -> subprocess.CompletedProcess:
    """Run a command without shell=True, capturing stdout and stderr."""
    return subprocess.run(xs, input=input, text=True, capture_output=True, check=check)
def need(x: str) -> bool:
    """Return True when command x is available on PATH."""
    return shutil.which(x) is not None
def uid(name: str) -> int:
    """Return the UID for a user name."""
    return pwd.getpwnam(name).pw_uid


def gid(name: str) -> int:
    """Return the GID for a group name."""
    return grp.getgrnam(name).gr_gid
def read(p: Path) -> bytes | None:
    """Read bytes from p, returning None when p does not exist."""
    return p.read_bytes() if p.exists() else None


def write(p: Path, b: bytes, mode: int = 0o644, owner: str | None = None) -> None:
    """Atomically write bytes to p, then set mode and optional owner."""
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(b); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp, mode)
        if owner:
            os.chown(tmp, *ids(owner))
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def render(s: str, c: dict) -> str:
    """Render a $PLACEHOLDER template string from config values."""
    m = {k.upper(): str(v) for k, v in c.items() if isinstance(v, (str, int))}
    return Template(s).safe_substitute(m)
def ids(spec: str) -> tuple[int, int]:
    """Parse 'user:group' into numeric uid/gid."""
    u, _, g = spec.partition(":")
    return uid(u), gid(g or u)


def same_meta(p: Path, owner: str, mode: int) -> bool:
    """Return True when p has the desired owner/group and permission mode."""
    if not p.exists(): return False
    st, (u, g) = p.stat(), ids(owner)
    return (st.st_uid, st.st_gid, st.st_mode & 0o777) == (u, g, mode)
def apt_missing(pkgs: list[str]) -> list[str]:
    """Return apt packages from pkgs that are not installed."""
    miss = []
    for p in pkgs:
        cp = cmd(["dpkg-query", "-W", "-f=${Status}", p])
        if cp.returncode != 0 or "install ok installed" not in cp.stdout:
            miss.append(p)
    return miss


def apt_install(pkgs: list[str]) -> dict:
    """Install missing apt packages and return a result dictionary."""
    if not pkgs: return res("apt packages")
    cp = cmd(["apt-get", "update"])
    if cp.returncode != 0: return res("apt packages", "error", cp.stderr.strip())
    cp = cmd(["apt-get", "install", "-y", *pkgs])
    return res("apt packages", "changed" if cp.returncode == 0 else "error", cp.stderr.strip())
def unit_text(c: dict) -> str:
    """Render the dev-container.service systemd unit text."""
    return f"""[Unit]
Description=devbox Docker Compose workstation container
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
User={c['dev']}
Group={c['dev']}
WorkingDirectory={c['run']}
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
def report(rs: list[dict]) -> int:
    """Print operation results and return a process exit code."""
    icons = {"ok": "✓", "would_change": "~", "changed": "+", "warn": "!", "error": "✗"}
    for r in rs:
        detail = f" — {r['detail']}" if r.get("detail") else ""
        print(f"{icons.get(r['state'], '?')} {r['state']:<12} {r['name']}{detail}")
    counts = {s: sum(r["state"] == s for r in rs) for s in ["ok", "would_change", "changed", "warn", "error"]}
    print("\n" + " ".join(f"{k}={v}" for k, v in counts.items() if v))
    return 1 if counts.get("error") else 0
def next_steps(c: dict, rs: list[dict]) -> None:
    """Print concise manual follow-up steps after the report."""
    home = c["home"]
    steps = []
    if not (home/".ssh/sign.pub").exists(): steps.append(f"create/copy SSH signing public key: {home}/.ssh/sign.pub")
    if any(r["name"] == "command gh" and r["state"] == "ok" for r in rs): steps.append(f"as {c['dev']}, run `gh auth status` or `gh auth login` if needed")
    steps.append("after starting the service, enter it with `make shell`")
    if steps:
        print("\nNext steps:")
        for s in steps: print(f"- {s}")
def main(argv=None) -> int:
    """Run the devbox sync command."""
    a = cli(argv)
    c = cfg(a)
    ops = plan(c, target(c["cmd"]))
    rs = run_ops(ops, c, c["apply"])
    rc = report(rs)
    next_steps(c, rs)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
