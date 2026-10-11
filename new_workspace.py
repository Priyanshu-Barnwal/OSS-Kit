#!/usr/bin/env python3
"""Create a Guide workspace for an open-source repo: ~/oss/<name>/{repo,knowledge,...}.

Clones via the personal SSH alias, sets the personal git identity on the clone, copies the
knowledge templates, CLAUDE.md and skills, and builds the code graph.
Standard library only (plus git, and graphify unless --no-graph).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parent
REPO_RE = re.compile(r"^[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}$")
NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("$ " + " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=cwd, check=True)


def render(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", help="owner/name of the upstream repo")
    ap.add_argument("--name", help="workspace directory name (default: repo name)")
    ap.add_argument("--no-graph", action="store_true", help="skip graphify (run /onboard L0 later)")
    args = ap.parse_args()

    if not REPO_RE.match(args.repo) or args.repo.endswith((".", "..")):
        sys.exit(f"invalid repo: {args.repo!r} (expected owner/name)")
    name = args.name or args.repo.split("/", 1)[1]
    if not NAME_RE.match(name) or name in (".", "..", "_kit"):
        sys.exit(f"invalid workspace name: {name!r}")

    cfg = json.loads((KIT / "config.json").read_text())
    ws = Path(os.path.expanduser(cfg["workspaces_dir"])).resolve() / name
    if ws.exists():
        sys.exit(f"{ws} already exists; pick another --name or remove it yourself")

    repo = ws / "repo"
    ws.mkdir(parents=True)
    try:
        run(["git", "clone", f"git@{cfg['ssh_host']}:{args.repo}.git", str(repo)])
    except subprocess.CalledProcessError:
        shutil.rmtree(ws)
        sys.exit("clone failed (check the repo name and `ssh -T git@%s`)" % cfg["ssh_host"])
    run(["git", "-C", str(repo), "config", "user.name", cfg["git_name"]])
    run(["git", "-C", str(repo), "config", "user.email", cfg["git_email"]])
    with open(repo / ".git" / "info" / "exclude", "a") as f:
        f.write("\n# oss guide workspace (local only)\ngraphify-out/\n")

    values = {
        "REPO": args.repo,
        "DATE": date.today().isoformat(),
        "PROFILE_PATH": cfg["profile_path"],
        "GH_CONFIG_DIR": cfg["gh_config_dir"],
    }
    shutil.copytree(KIT / "templates" / "knowledge", ws / "knowledge")
    (ws / "CLAUDE.md").write_text(render((KIT / "templates" / "CLAUDE.md").read_text(), values))
    for skill in sorted((KIT / "skills").iterdir()):
        dest = ws / ".claude" / "skills" / skill.name
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text(render((skill / "SKILL.md").read_text(), values))
    (ws / "tools").symlink_to(KIT / "tools", target_is_directory=True)
    (ws / "scratch").mkdir()
    (ws / "graphify-out").symlink_to(Path("repo") / "graphify-out", target_is_directory=True)

    if not args.no_graph:
        if shutil.which("graphify"):
            run(["graphify", "update", "repo"], cwd=ws)
            run([sys.executable, str(KIT / "tools" / "graph_map.py"), "--workspace", str(ws)])
        else:
            print("graphify not found; run /onboard L0 after installing it", file=sys.stderr)

    print(f"\nWorkspace ready: {ws}\n  cd {ws} && claude\n  then: /onboard")


if __name__ == "__main__":
    main()
