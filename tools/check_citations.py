#!/usr/bin/env python3
"""Check that `path:line` citations in knowledge/ notes still point at real code.

Citation format (paths relative to repo/):
    `src/pkg/client.py:42`            single line
    `src/pkg/client.py:42-60`         range
    `src/pkg/client.py:42#Client.chat` line + symbol that must appear near it

Also flags notes whose cited files changed since the note's `last_verified_commit`.
Standard library only. Exit code 1 if any citation is broken.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CITE_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?(?:#([A-Za-z_][\w.]*))?`")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
FRONT_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
SYMBOL_WINDOW = 3


def frontmatter(text: str) -> dict:
    m = FRONT_RE.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def changed_since(repo: Path, sha: str) -> set[str] | None:
    proc = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", sha, "HEAD"],
                          capture_output=True, text=True)
    return set(proc.stdout.split()) if proc.returncode == 0 else None


def check_citation(repo: Path, path: str, start: int, end: int, symbol: str | None) -> str | None:
    target = (repo / path).resolve()
    if not target.is_relative_to(repo):
        return "path escapes repo/"
    if not target.is_file():
        return "file not found"
    lines = target.read_text(errors="replace").splitlines()
    if start < 1 or end > len(lines) or start > end:
        return f"line out of range (file has {len(lines)} lines)"
    if symbol:
        name = symbol.rsplit(".", 1)[-1]
        window = lines[max(0, start - 1 - SYMBOL_WINDOW): end + SYMBOL_WINDOW]
        if not any(re.search(rf"\b{re.escape(name)}\b", ln) for ln in window):
            return f"symbol '{symbol}' not found near line {start} (code moved?)"
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", type=Path, default=Path.cwd())
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    repo, kb = (ws / "repo").resolve(), ws / "knowledge"
    if not repo.is_dir() or not kb.is_dir():
        sys.exit(f"{ws} is not a workspace (needs repo/ and knowledge/)")

    report = {"broken": [], "stale": [], "unverified": [], "checked": 0}
    for note in sorted(kb.rglob("*.md")):
        if note.name.startswith("_"):  # templates
            continue
        text = note.read_text(errors="replace")
        rel_note = str(note.relative_to(ws))
        cited_files = set()
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in CITE_RE.finditer(line):
                path, start = m.group(1), int(m.group(2))
                end = int(m.group(3) or start)
                report["checked"] += 1
                cited_files.add(path)
                err = check_citation(repo, path, start, end, m.group(4))
                if err:
                    report["broken"].append({"note": rel_note, "line": lineno, "cite": m.group(0), "error": err})

        if not cited_files:
            continue
        sha = frontmatter(text).get("last_verified_commit", "")
        if not SHA_RE.match(sha):
            report["unverified"].append(rel_note)
            continue
        changed = changed_since(repo, sha)
        if changed is None:
            report["unverified"].append(rel_note)
        elif cited_files & changed:
            report["stale"].append({"note": rel_note, "since": sha, "changed": sorted(cited_files & changed)})

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Checked {report['checked']} citations.")
        for b in report["broken"]:
            print(f"BROKEN  {b['note']}:{b['line']}  {b['cite']}  -> {b['error']}")
        for s in report["stale"]:
            print(f"STALE   {s['note']}  (cited files changed since {s['since'][:8]}: {', '.join(s['changed'])})")
        for u in report["unverified"]:
            print(f"UNVERIFIED  {u}  (no valid last_verified_commit)")
        if not (report["broken"] or report["stale"] or report["unverified"]):
            print("All good.")
    sys.exit(1 if report["broken"] else 0)


if __name__ == "__main__":
    main()
