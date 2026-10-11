---
name: onboard
description: Build this workspace's knowledge base layer by layer (L0 graph, L1 orientation, L2 architecture, L3 flows, L4 conventions, L5 gotchas) while teaching the user. Resumes at the next unfinished layer.
argument-hint: "[L0|L1|L2|L3|L4|L5]"
---

# /onboard

Follow the rules in `CLAUDE.md`. Arguments: `$ARGUMENTS`.

## Start of every run
1. Read `knowledge/progress.md` and the skill profile.
2. Pick the layer: the one named in the arguments, else the first layer not marked `done`.
3. Tell the user in 2-3 lines: which layer, what they'll get from it, rough time. Then start.
4. **Do one layer per session** (L3: one flow per session). When it's done, update
   `progress.md` (status `done`, date, one-line note), run `python3 tools/check_citations.py`,
   fix anything broken, and suggest `/clear` before the next layer.

Record `HEAD=$(git -C repo rev-parse HEAD)` at the start. Use it as `last_verified_commit` for notes you verify.

---

## L0: Code graph (5 min, mostly automatic)
1. If `repo/graphify-out/graph.json` is missing, or `git -C repo log -1 --format=%cI` is newer than it, run
   `graphify update repo` from the workspace root. (Code-only AST extraction: free, no LLM.)
2. Ensure `graphify-out` → `repo/graphify-out` symlink exists and `graphify-out/` is in
   `repo/.git/info/exclude`.
3. Run `python3 tools/graph_map.py`. If most modules land in `(root)` or one giant module, re-run
   with `--depth 1` or `--depth 3` and pick the depth that gives 5-20 meaningful modules.
4. Show the user: node/edge counts, the top 5 god nodes from `graphify-out/GRAPH_REPORT.md`, and
   the module list. Say plainly that this is a **map, not understanding**: L1-L3 verify it.

## L1: Orientation (about 45 min)
Goal: the user knows what this project is for and has it running locally.
1. Read the README, docs index, `pyproject.toml`/`setup.cfg`/`package.json`, CI config
   (`.github/workflows/*`) and CONTRIBUTING's dev-setup section. CI shows the *real* test commands.
2. Explain: what problem it solves, who uses it, the 3 most common ways it's used (from README examples).
3. **Ask before installing.** Then set up `.venv/` in the workspace (not in `repo/`) using the
   project's own documented method and extras for development/testing.
4. Run the test suite (or a fast subset if it takes over 5 min; use the CI command as a guide). Record pass/fail counts.
   Failures from missing services/keys are normal: note them, don't fix them.
5. Exercise for the user: run one README example themselves (in `scratch/`) and change one argument.
6. Write `knowledge/overview.md` with the **commands that actually worked** and every setup problem hit.
7. Optional checkpoint (offer it): e.g. "What would you tell a colleague this project is for?",
   "Which command runs a single test file?"

## L2: Architecture (about 60 min)
Goal: the user can name the main modules, say what each owns, and say where requests enter.
1. Inputs: `knowledge/map.json`, `graphify-out/GRAPH_REPORT.md` (god nodes, communities, surprising
   connections), the package layout, and public API exports (`__init__.py`, `__all__`).
2. For each non-test module (largest/most-connected first): read its key symbols' code, write a
   one-line `responsibility` into `map.json`, and cite the evidence.
3. Communities are unnamed ("Community 3"). Name the meaningful ones by what their nodes do.
4. Identify **entry points**: public API, CLI, server routes, plugin/entry-point registration.
5. Check dependency direction: for the top `depends_on` edges, confirm in code (imports/calls).
   List `INFERRED`-only edges under "Unverified / inferred relationships".
6. Teaching moves:
   - Before showing your module table, show the module **names** and ask the user to guess each
     one's job. Then compare.
   - Exercise: "Where would you add <a plausible new feature>?" Discuss their answer against the map.
7. Write `knowledge/architecture.md` (summary, module table, entry points, ASCII diagram,
   unverified section) and fill in glossary terms you encountered.
8. Optional checkpoint.

## L3: Key flows (about 45 min per flow, 3-5 flows, one per session)
Goal: the user can trace the most common operations from entry point to exit.
1. First time in L3: propose 3-5 candidate flows from README examples, the most-tested public
   functions and entry points. Prefer ones that touch the user's **stretch** skills
   (e.g. async/streaming, concurrency, LLM calls). The user picks. Record the list in `progress.md`.
2. For the chosen flow:
   a. Skeleton: `graphify path "<entry symbol>" "<exit symbol>"` and `graphify query "<flow question>" --budget 1500`.
   b. Read the code along the path. Fill in the steps the graph missed (dynamic dispatch, callbacks).
   c. **Verify by running**: a small script in `scratch/` (or a focused test with `-s`) that exercises the
      flow with logging or `breakpoint()`, and stubs network/LLM calls if needed. Mark steps ✅ only
      when you observed them.
   d. Concurrency/async: identify which thread/event loop each step runs on, what's shared, and what's locked.
3. Teaching moves: at each hop, ask "what do you think gets called next?" before revealing.
   Exercise: user sets a breakpoint at step N and inspects a value you name.
4. Write `knowledge/flows/<slug>.md` from `knowledge/flows/_template.md`.
5. Optional checkpoint. Mark L3 `done` only after all chosen flows are written.

## L4: Conventions (about 45 min)
Goal: the user's first PR looks like it was written by a regular contributor.
1. Static sources: CONTRIBUTING, PR template (`.github/pull_request_template.md`), lint/format/type
   configs (ruff/black/mypy/pre-commit), CI jobs, CODEOWNERS, changelog process, CLA/DCO, and any
   AI-contribution policy (`AGENTS.md`, CONTRIBUTING).
2. Review mining: list the ~30 most recent merged PRs, preferring non-maintainer authors:
   `GH_CONFIG_DIR=... gh pr list -R {{REPO}} --state merged --limit 60 --json number,title,author,additions,deletions,url`
   Hand batches of ~10 to general-purpose subagents. Each fetches review comments
   (`gh api repos/OWNER/NAME/pulls/N/comments` and `/reviews`) and returns **recurring reviewer requests
   with PR links**, not summaries of each PR. Also note typical PR size and how long review took.
3. Read 2-3 representative test files to extract the testing style (fixtures, mocks, naming, markers).
4. Write `knowledge/conventions.md`. Every "reviewers want X" needs at least 2 PR links.
5. Exercise: show the user a real reviewed diff (with the review comments hidden) and ask what a reviewer would flag.

## L5: Gotchas (about 30 min)
Goal: the user knows where the traps are before stepping on one.
1. Sources (run from `repo/`):
   - churn hotspots: `git log --since=1.year --format= --name-only | sort | uniq -c | sort -rn | head -20`
   - fixes and reverts: `git log --since=1.year --oneline -i -E --grep='fix|revert|regression|race|deadlock'`
   - markers: grep for `HACK|XXX|FIXME|workaround|noqa|type: ignore` (counts by file; read the interesting ones)
   - long-open bugs: `GH_CONFIG_DIR=... gh issue list -R {{REPO}} --label bug --state open --search "sort:created-asc" --limit 15`
2. For anything that looks odd, use `git log -L` / `git blame` to find the commit and PR that explain it.
3. Write `knowledge/gotchas.md`: what, where (`file:line`), why (link), how to avoid. Put things you
   can't explain into `knowledge/open-questions.md`.
4. Wrap-up: summarise what the user now knows (from `progress.md`) and what's next: the Issue
   Analyst workflow, or `/tour` on weak spots.
