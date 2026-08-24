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
  **CONFIRMED 2026-08-24 ~19:00 UTC, definitive negative result:**
  re-checked `get_session(cse_01LFv3QXjUowxWUHD4XwLMym)` (ran 18:04:05-
  18:20:29, $3.91, 75k output tokens, ended IDLE/REVIEW_READY -- not
  crashed) against `list_commits` for that exact window. Only two commits
  landed in 18:04-18:20 (`850607a` GOALS.md, `f5c0acd` .gitignore), and
  BOTH carry an explicit `Claude-Session: https://claude.ai/code/
  session_01Xi9RuUYcgbdgDMPdh32DnD` trailer -- a direct attribution to the
  INTERACTIVE session, not the Routine. This resolves the earlier
  ambiguity conclusively: **the Routine session ran for 16 real minutes
  and produced ZERO commits of its own.** The "don't give up silently,
  commit what you have" prompt fix added earlier today DID NOT WORK.
  Reported to Het directly: the unattended dev-loop Routine cannot yet be
  trusted to make progress while he's away, even though it runs cleanly
  and doesn't crash. Root cause still unknown -- the permission-classifier
  timeout observed interactively during this same session is a plausible
  cause but NOT yet proven to be what happens inside the Routine's own
  container. Next session: this needs actual root-causing, not another
  blind re-fire-and-hope. If a way exists to inspect the Routine session's
  own transcript/tool-call log (not just get_session's metadata), that's
  the highest-value thing to check next.
  **2026-08-24 ~19:23 UTC: targeted fix attempt #2, this time with a
  specific mechanism, not a vague instruction.** Updated the Routine's
  prompt (trig_013GUxs9AwHaRvb1o4eGJRGx) to name the EXACT error text
  observed interactively ("temporarily unavailable... auto mode cannot
  determine the safety... try this action again") and give an explicit
  retry protocol: wait 5-10s, retry the identical call, up to 5 times,
  before treating it as blocked. Also gave it a specific, easily-verified
  test task (append one dated self-test line to AUTONOMOUS_LOG.md) instead
  of open-ended P0 work, so success/failure is unambiguous this time. Fired
  immediately via fire_trigger rather than waiting for the next scheduled
  slot -- session `cse_01RJf6KJXJSv3YveSfSHuLxj`, started 19:23:07 UTC.
  **Result: TBD, check get_session + list_commits after it completes.**

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
