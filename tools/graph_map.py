#!/usr/bin/env python3
"""Build knowledge/map.json (module -> files, key symbols, dependencies) from the graphify graph.

Deterministic skeleton only: the Guide fills in each module's `responsibility`.
Re-running keeps existing `responsibility` and `notes` fields.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

MAX_FILES = 50
TOP_SYMBOLS = 8
TEST_MARKERS = ("test", "tests", "testing")


def module_of(rel: Path, depth: int) -> str:
    parts = rel.parent.parts[:depth]
    return "/".join(parts) if parts else "(root)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", type=Path, default=Path.cwd())
    ap.add_argument("--depth", type=int, default=2, help="directory depth that defines a module")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    repo = (ws / "repo").resolve()
    graph_path = repo / "graphify-out" / "graph.json"
    if not graph_path.is_file():
        sys.exit(f"no graph at {graph_path}; run `graphify update repo` from {ws}")
    g = json.loads(graph_path.read_text())

    node_mod: dict[str, str] = {}
    files: dict[str, set[str]] = defaultdict(set)
    communities: dict[str, set] = defaultdict(set)
    labels: dict[str, str] = {}
    for n in g["nodes"]:
        src = n.get("source_file")
        if not src:
            continue
        try:
            rel = Path(src).resolve().relative_to(repo)
        except ValueError:
            continue
        mod = module_of(rel, args.depth)
        node_mod[n["id"]] = mod
        files[mod].add(str(rel))
        labels[n["id"]] = n.get("label", n["id"])
        if n.get("community") is not None:
            communities[mod].add(n["community"])

    degree: Counter = Counter()
    deps: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for e in g.get("links", g.get("edges", [])):
        s, t = e.get("source"), e.get("target")
        degree[s] += 1
        degree[t] += 1
        ms, mt = node_mod.get(s), node_mod.get(t)
        if ms and mt and ms != mt and e.get("relation") != "contains":
            deps[ms][mt][e.get("confidence", "UNKNOWN").lower()] += 1

    map_path = ws / "knowledge" / "map.json"
    old = json.loads(map_path.read_text()).get("modules", {}) if map_path.is_file() else {}
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    modules = {}
    for mod in sorted(files):
        file_list = sorted(files[mod])
        symbols = sorted((nid for nid, m in node_mod.items() if m == mod and not labels[nid].endswith(".py")),
                         key=lambda nid: -degree[nid])[:TOP_SYMBOLS]
        modules[mod] = {
            "responsibility": old.get(mod, {}).get("responsibility", "TODO"),
            "notes": old.get(mod, {}).get("notes", ""),
            "is_test": any(p in TEST_MARKERS for p in mod.split("/")),
            "file_count": len(file_list),
            "files": file_list[:MAX_FILES],
            "key_symbols": [f"{labels[nid]} ({degree[nid]})" for nid in symbols],
            "communities": sorted(communities[mod]),
            "depends_on": {m: dict(c) for m, c in sorted(deps[mod].items(), key=lambda kv: -sum(kv[1].values()))},
        }

    map_path.parent.mkdir(exist_ok=True)
    map_path.write_text(json.dumps({"generated_from_commit": head, "module_depth": args.depth,
                                    "modules": modules}, indent=2))
    print(f"Wrote {map_path} ({len(modules)} modules, commit {head[:8]})")


if __name__ == "__main__":
    main()
