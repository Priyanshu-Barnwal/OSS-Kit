---
name: tour
description: Interactive walkthrough of one area, feature or question in this codebase, grounded in real code with predict-then-check and a hands-on exercise. Optionally saves what was learned to the knowledge base.
argument-hint: "<topic or question, e.g. 'how retries work'>"
---

# /tour

Follow the rules in `CLAUDE.md`. Topic: `$ARGUMENTS` (if empty, offer 3 topics based on weak or
unreviewed entries in `knowledge/progress.md`).

1. **Start from what's known.** Check `knowledge/` (architecture, flows, glossary, gotchas) for
   the topic. If a note covers it, say so and build on it rather than re-deriving.
2. **Locate.** `graphify query "$ARGUMENTS" --budget 1500`, then Grep/Glob to confirm. Pick the 3-6
   places that matter. Don't tour the whole module.
3. **Orient (1 message).** What this area is for, where it sits in the architecture, and the stops
   you'll visit (as `file:line` citations).
4. **Walk the stops one at a time.** At each stop:
   - Ask the user to predict something concrete (what it returns, what calls it, what happens on error).
   - Show the relevant lines (short excerpts, cited) and compare with their prediction.
   - Point out the "why" when history explains it (`git log -L`, linked PR).
   Wait for the user's reply between stops; don't run ahead.
5. **Exercise.** One hands-on task they run: a breakpoint, a tweak in `scratch/`, or a focused test
   with `-s`. For async/concurrency topics, make it observable (log thread/task names, timings).
6. **Wrap up.** A 3-line summary, plus an optional 2-3 question check (skippable).
7. **Save (ask first).** Offer to add verified findings to the right note (`flows/`, `gotchas.md`,
   `glossary.md`, `architecture.md`) with citations and ✅/📖 tags, update `last_verified_commit`,
   and add/update the topic row in `progress.md` (confidence 1-5 from the user's own rating).
