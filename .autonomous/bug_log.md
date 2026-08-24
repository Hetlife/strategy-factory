# Bug log (append-only) — what broke, what fixed it, what's still open

Separate from `AUTONOMOUS_LOG.md` (terse action-by-action record) and
`AUTONOMOUS_TODO.md` (narrative decisions). This file is specifically for
defects found in the system's own logic — so a future session (or Het)
can see at a glance what's already been caught and fixed vs. what's still
live. Format: `STATUS | date found | short id | what broke | fix / next step`.

---

## OPEN

- **OPEN | 2026-08-24 | autonomous-routine-zero-commits** — the scheduled
  Routine has fired multiple times, run for real minutes with real token
  spend, and ended cleanly (not crashed) but produced ZERO commits each
  time. Hypothesis: Bash permission-classifier friction that an unattended
  session (no human to approve a prompt) can't route around. Mitigation
  attempted: updated the Routine's prompt with explicit "don't give up
  silently, try alternatives, commit what you have with a note about the
  blocker if truly stuck" instructions, re-fired as
  `cse_01LFv3QXjUowxWUHD4XwLMym`. **Not yet confirmed fixed** — check
  `get_session` status + `mcp__github__list_commits` on this branch for
  activity after that firing before trusting unattended operation.
  **Supporting evidence found interactively, same day:** while committing
  P0-3, a `git push` call hit a real error — "claude-sonnet-5 is temporarily
  unavailable (timed out), so auto mode cannot determine the safety of Bash
  right now" — i.e. the permission classifier itself timed out. In an
  INTERACTIVE session this just meant retrying the identical command a
  moment later, which then succeeded immediately. In an unattended Routine
  firing with nobody watching, a classifier timeout on the git commit/push
  step specifically would look exactly like this bug: real time and tokens
  spent, a clean-looking end state, zero commits landed. This strengthens
  the permission-friction hypothesis considerably — it's no longer just a
  guess, it's now been directly observed.
  **Checked 2026-08-24 ~18:46 UTC:** `get_session(cse_01LFv3QXjUowxWUHD4XwLMym)`
  shows it ran 18:04-18:20, real spend ($3.91, 75k output tokens), ended
  `SESSION_STATUS_IDLE` / `REVIEW_READY` (unread). But its window overlaps
  this exact interactive session's own commits (GOALS.md, .gitignore,
  agents/ team all landed 18:06-18:21), and every Claude Code commit
  carries identical author metadata ("Claude" <noreply@anthropic.com>)
  regardless of session -- `list_commits` cannot disambiguate which of
  those commits, if any, came from the Routine vs. this session. No
  completion notification was queued either. **Still not confirmed either
  way** -- a real tooling gap (no way from here to read a sibling session's
  transcript), not a resolved bug. Next session: fire an isolated test with
  a deliberately narrow, easily-attributable change (e.g. a distinctive
  one-line comment) during a window with no interactive session running
  concurrently, then check for that exact string in the commit log.

## FIXED

- **FIXED | 2026-08-24 | cost-model-understated-3x** — flat `COST_PER_SIDE`
  understated real transaction cost by up to ~3x at small (rung-1) position
  sizes because real Indian equity delivery cost has a FIXED per-scrip
  component (DP charge) a flat percentage can't represent. Fixed by
  `round_trip_cost()` = variable % + fixed Rs/scrip. Verified against
  EXECUTION_PLAN.md's own acceptance criterion. Commit `38dee23`.
- **FIXED | 2026-08-24 | sharpe-variance-floor** — Sharpe computed on a thin
  sample could hit near-zero variance and blow up to an absurd value
  (~106,512 seen in testing), which could have produced a false PROMOTE.
  Fixed with `MIN_SHARPE_SAMPLE_DAYS=20` NaN guard. Commit `5669fb0`.
- **FIXED | 2026-08-24 | cost-efficiency-advisor-miscount** — advisors.py's
  cost-efficiency heuristic counted any nonzero-return day as a "trade,"
  not actual turnover events, understating true cost-per-round-trip. Fixed
  to use actual turnover-based trade count.
- **FIXED | 2026-08-24 | backtest-silent-exceptions** — `advisors.py`'s
  `backtest()` swallowed exceptions from `sig_*` functions with no
  visibility. Added warning logging (`n_errors` count printed).
- **FIXED | 2026-08-24 | lineage-lost-on-demote-reset** — a paper-tier
  contestant demoted back to a fresh attempt (`blank_stats()`) lost its
  recorded `lineage`, breaking family-tree tracking across generations.
  Fixed by threading `lineage=s["lineage"]` through the reset.
  Commit `1b7d29e`.
- **FIXED | 2026-08-24 | promotion-children-no-lineage** — children spawned
  by `spawn_children()` on promotion had no `lineage` recorded at all (only
  advisor-evolved and crossover children did). Fixed by setting
  `con[k] = blank_stats(lineage=...)` after `spawn_children()` calls.
  Commit `1b7d29e`.
- **FIXED | 2026-08-24 | crossover-name-chaining** — crossover child names
  chained unboundedly across generations (`a_x_b_x_c_x_d...`). Fixed by
  truncating parent names to `[:18]` chars + a generation suffix.
  Commit `1b7d29e`.
- **FIXED | 2026-08-24 | dashboard-auth-test-invalid** — attempted to verify
  `dashboard.py`'s private-repo raw-URL auth via `curl` from inside this
  sandbox; got HTTP 200 and initially treated that as conclusive. Then
  found `GH_TOKEN=proxy-injected` in the sandbox env — the outbound proxy
  transparently authenticates GitHub requests, so a sandbox curl succeeding
  proves nothing about what a real anonymous visitor sees. Corrected the
  record before it could be mistaken as resolved; now a standing
  `state.json.standing_env_facts` entry. Commit `6ec9d6f`.
- **FIXED | 2026-08-24 | stray-pycache-untracked** — a stop-hook flagged
  untracked `__pycache__/` files. Added `.gitignore`, removed the
  directory. Commit `f5c0acd`.
