# Guide kit

Shared kit for per-project contribution workspaces. The Guide runs in your **main Claude Code
session** (not as a subagent) because it's interactive: it uses `CLAUDE.md` for its rules and
skills (`/onboard`, `/tour`) for its modes.

## New workspace
```bash
python3 ~/oss/_kit/new_workspace.py OWNER/REPO        # clone, templates, skills, code graph
cd ~/oss/REPO && claude
/onboard          # L0 graph → L1 orientation → L2 architecture → L3 flows → L4 conventions → L5 gotchas
/tour <topic>     # interactive walkthrough of one area
```

## Workspace layout
```
~/oss/<repo>/
├── repo/               clone (origin = upstream), personal git identity, read-only for the Guide
├── knowledge/          shared knowledge base (Guide writes; Issue Analyst reads)
├── graphify-out -> repo/graphify-out   code graph (excluded via repo/.git/info/exclude)
├── tools -> ~/oss/_kit/tools           check_citations.py, graph_map.py
├── scratch/            throwaway experiment scripts
├── .claude/skills/     onboard, tour (copied from the kit, rendered for this repo)
└── CLAUDE.md           Guide rules for this repo
```

## Kit contents
| Path | What |
|---|---|
| `config.json` | personal GitHub user, `gh` config dir, SSH alias, git identity (noreply email), profile path |
| `new_workspace.py` | bootstrap script |
| `templates/` | `CLAUDE.md` + `knowledge/` note templates |
| `skills/` | `onboard`, `tour` |
| `tools/check_citations.py` | verifies `` `path:line#Symbol` `` citations; flags notes whose cited files changed since `last_verified_commit` |
| `tools/graph_map.py` | builds `knowledge/map.json` from the graph; keeps the Guide's `responsibility` annotations on re-run |

Skills are **copied** into each workspace when it's created. After editing a kit skill, copy it into
existing workspaces (re-render `{{REPO}}` etc.). Tools are symlinked, so edits apply everywhere at once.

## Notes
- `graphify update repo` is code-only AST extraction (no LLM, no cost). Communities come out
  unnamed, and the Guide names them in L2. Call edges are `INFERRED` even in the AST pass.
- Planned next: `/quiz`, `/refresh` (graphify update + check_citations + re-verify stale notes), `/briefing <issue>`.
