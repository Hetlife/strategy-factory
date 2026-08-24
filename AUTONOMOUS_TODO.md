# STRATEGY FACTORY — AUTONOMOUS TODO (narrative companion)

**Read order, cheapest first:**
1. `.autonomous/state.json` — structured, current, cheap. Queue, decisions
   index, recent commits, test status, next-action hint. Read this first,
   always.
2. `CLAUDE.md` — binding rules, architecture, hard constraints. Static,
   rarely changes. Claude Code auto-loads it.
3. `AUTONOMOUS_LOG.md` — one line per past session, `tail -30` it instead
   of running `git log` and re-parsing full commit messages.
4. **This file** — only when you need the full prose rationale behind a
   decision, or before extending something non-obvious. Don't read it
   reflexively every session; it's prose, it costs more tokens than the
   files above, and its facts are duplicated in structured form in
   `state.json` already.

Update discipline: routine "did task X" bookkeeping goes in
`AUTONOMOUS_LOG.md` (one line) + `.autonomous/state.json` (structured
fields). Only add prose here for something genuinely narrative-worthy —
a new decision with real tradeoffs, a non-obvious architecture note. This
file should grow slowly; if you're about to write a paragraph restating
what a commit message already says, don't.

## Decisions Made (full rationale — the reason this file exists)

- **Law 1 override (advisor layer trains on historical price data):**
  explicitly requested and authorized by Het after being shown the
  tradeoff directly (a Q&A comparing "train on own live track record" vs.
  "train on raw historical price data" — Het chose the latter).
  Mitigation kept: parameter grids stay inside the same mechanism-bounded
  ranges the seed registry already uses; one of the three advisor
  heuristics specifically scores regime-robustness. Commit `00f5651`.
- **Law 2 override (evolution replaces underperformers):** explicitly
  requested by Het ("we want them to be mutated..."). Mitigation *I*
  chose, not asked again: mechanically still only ever creates a new
  registry key (never edits one in place), restricted to paper-tier
  (rung 0) contestants only — real-money rungs are excluded entirely and
  still only evolve via `spawn_children()`. Commit `00f5651`.
- **PR #1 merge:** asked directly twice. First answer was "yes, merge
  it," but an ambiguous "let's start again darling" arrived mid-merge-prep
  before I acted on it, so I re-asked rather than guess — final answer was
  **hold off**. Treat this as live until a *fresh* session gets an
  unambiguous confirmation; a prior session's "yes" does not carry
  forward, ever, regardless of how this reads in hindsight.
- **`spawn_children()` input_cost coverage gap:** treated as a
  completeness gap, not a values decision — the seed grid only ever had
  one `input_cost` instance, so no breeding rule had been written for it.
  Extended using the same mechanism-bounded pattern the other families
  use. `monsoon` deliberately still excluded (dormant, no CSV). Commit
  `4a69110`.
- **`train_brain.py` removal:** its own source doc framed this as an
  open choice ("fix it... or remove it"). Removed — fully superseded by
  `advisors.py`, which is actually wired in, uses 3 heuristics instead of
  one grid-search winner, and doesn't have the known typo. Reversible via
  git history. Commit `85cd1a5`.
- **Efficiency infrastructure (this pass):** `CLAUDE.md`/
  `01_objectives.txt`/`02_architecture.txt`/`03_learnings_and_suggestions
  .txt` were uploaded chat files, never committed to the repo — every
  prior session's instruction to "read CLAUDE.md if present" silently
  failed and wasted a lookup. Committed a condensed `CLAUDE.md` as the
  permanent, self-contained source of truth for rules/architecture, added
  `.autonomous/state.json` (structured, cheap to read) and
  `AUTONOMOUS_LOG.md` (append-only, terse) so a fresh session's cost is
  one small JSON read + a 3-line git log check instead of ~1000 lines of
  prose across 4 files plus exploratory git commands.

## Architecture notes beyond CLAUDE.md

- `factory.py`: `blank_stats()` gained `lineage`/`evolved_out`/
  `trust_scored` fields, backfilled onto pre-existing ledger entries by
  `load_state()` — don't assume old entries have these without that
  backfill running.
- `factory_state/parameter_bank.json` and `advisor_state.json` don't
  exist on `main` yet (only on the PR branch), and `parameter_bank.json`
  doesn't exist anywhere yet — no training run has happened against real
  data. `dashboard.py` degrades gracefully (empty-state UI) when either
  is missing.
- Full narrative write-ups for the two biggest pieces of work so far live
  in `maintenance_notes/2026-08-23_status_note.md` (Sunday-report
  verification) and `maintenance_notes/2026-08-23_advisor_layer.md`
  (advisor layer design + Three Laws rationale, longer version of the
  decisions above).

## Ideas / Future Improvements (ranked below the P1/P2 queue in state.json)

- Dashboard: a "market regime" indicator, correlation matrix across live
  contestants, and an "upcoming autonomous actions" preview (what the
  *next* `report()` run would decide given current state).
- Advisor layer currently only blends numeric hyperparameters — never
  proposes switching a sector leader or trying a different strategy
  family. Real capability gain, but widens the mutation space
  significantly; would need its own Law-1/Law-2 conversation with Het
  first, same as the current advisor layer did.

## Session history

See `AUTONOMOUS_LOG.md` for the compact per-session log and `git log` for
full commit detail — not duplicated here.
