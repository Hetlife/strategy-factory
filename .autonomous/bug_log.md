# Bug log (append-only) — what broke, what fixed it, what's still open

Separate from `AUTONOMOUS_LOG.md` (terse action-by-action record) and
`AUTONOMOUS_TODO.md` (narrative decisions). This file is specifically for
defects found in the system's own logic — so a future session (or Het)
can see at a glance what's already been caught and fixed vs. what's still
live. Format: `STATUS | date found | short id | what broke | fix / next step`.

---

## OPEN

- **CLOSED (accepted, not fixed) | 2026-08-24 | autonomous-routine-zero-commits** — the scheduled
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
  **Result, checked 19:33 UTC: FAILED AGAIN, unambiguously this time.**
  Session ran 19:23:07-19:31:02 (8 real minutes, $1.73, 25.5k output
  tokens), ended cleanly (IDLE/REVIEW_READY). Zero commits landed after
  19:23:34 (this interactive session's own last commit) through the test
  session's end -- no overlapping-attribution ambiguity this time, since no
  other commit happened in that window from any source. The specific,
  named retry instruction for the classifier-timeout error did NOT produce
  a commit, even against a deliberately trivial, unambiguous test task.
  **This rules out (or at least shows insufficient) the classifier-timeout
  hypothesis as the full explanation** -- two different targeted fixes have
  now failed the same way. Decision: PAUSED this Routine
  (trig_013GUxs9AwHaRvb1o4eGJRGx, disabled via update_trigger) rather than
  keep re-firing blind guesses at real cost with no diagnostic gain. Real
  root-causing needs actual visibility into what the session did internally
  (its own transcript/tool calls), which isn't available through
  get_session's metadata-only view -- that's the actual blocker on
  progress here, not another prompt tweak.
  **2026-08-25 ~02:02 UTC: third failure, confirmed via git log.** Before
  the disable above landed, the Routine's normal 5-hourly schedule fired
  again on its own at 2026-08-25T00:49:16Z (`last_fired_at` per
  list_triggers). Checked git log on the branch spanning this interactive
  session's own last commit (30b9e18, 19:23:34Z) through now (02:02Z) --
  zero commits in that entire window, from any source. That's three
  consecutive failures now (the original 3 pre-session firings, this
  session's own targeted retry-fix test, and this unattended 00:49 firing
  on the SAME updated prompt). **Routine trig_013GUxs9AwHaRvb1o4eGJRGx is
  now DISABLED** via update_trigger (enabled=false) as of 2026-08-25
  ~02:02 UTC -- do not re-enable it without an actual root cause, not
  another prompt-wording guess. The daily-report Routine
  (trig_01Y9q1Dn98ghLMD4KX7xZfxp) is unaffected and stays enabled.
  **2026-08-25 ~02:16 UTC: diagnostic-first fix attempt #3 (4th firing
  overall) -- STILL zero commits, even for a trivially small pwd/git-status
  test file.** Session cse_01Ux9dNfUj9rgiNHyaoWErEh ran 02:10:28-02:14:46
  (4 min, $0.48), ended cleanly, committed nothing at all -- ruling out
  "the real task is too big/complex" as an explanation, since the ONLY
  instructed first action was a one-file diagnostic commit.
  **LIKELY ROOT CAUSE FOUND, 2026-08-25 ~02:16 UTC:** ran a controlled
  comparison -- fired an equivalent trivial diagnostic task via
  `create_session` (session_016SJaSRnEjJxpFtWeP6BCSM) with EXPLICIT
  `source_url`/`source_revision`/`outcome_branch` parameters, instead of
  `create_trigger`/`fire_trigger`. Checked its `session_context` before it
  even ran: it carried real `sources`/`outcomes` git-repository binding.
  Every `create_trigger`-fired session checked across all 4 failed
  attempts NEVER carried any such binding -- only
  `{autofix_on_pr_create, permission_mode}`. The create_session diagnostic
  completed in under a minute and its commit (03850e3, "docs: create-session
  diagnostic test log entry") was independently verified via list_commits,
  landing 40s after session creation. **This is the strongest evidence yet:
  create_trigger sessions are not given a bound git repository/branch the
  way create_session sessions are** -- the tool schema for create_trigger
  has no source_url/outcome_branch parameter at all, unlike create_session.
  The Routine's prompt has always assumed the repo already exists at a
  known path (reading CLAUDE.md etc. as step 1) rather than explicitly
  cloning it -- if there's no bound checkout, that assumption is simply
  false for every one of these firings.
  **PROPOSED FIX** (was: not yet tested, on hold pending Het's ok):
  rewrite the Routine's prompt to explicitly
  `git clone https://github.com/Hetlife/strategy-factory.git` (using the
  proxy-injected GH_TOKEN auth) and `git checkout` the target branch as
  its literal first action, rather than assuming a checkout exists.
  **2026-08-25 ~11:03 UTC: FIX WAS TESTED, AND FAILED.** The primary
  interactive session updated the Routine's prompt to this explicit
  clone-first protocol and fired it (`trig_013GUxs9AwHaRvb1o4eGJRGx`,
  `last_fired_at: 2026-08-25T11:03:48Z`). Checked independently from a
  separate session: `git fetch origin --prune` (picked up `main` as a new
  remote branch from the PR #1 merge) and
  `git log --all --grep="clone-fix" -i` and `--grep="routine-clone-fix"`
  across every local+remote ref found **zero matching commits anywhere**.
  The Routine's own STEP 4 instruction was to append a specific,
  distinctively-named log line and push it -- that never landed, on any
  branch. **This rules out repo-binding-alone as the full explanation.**
  Even with a session that explicitly clones and checks out the correct
  branch as literally its first instructed action, it still produced zero
  commits. Two independent, structurally different fixes (retry-tuning,
  then explicit-clone) have now both failed the same way. The actual
  blocker remains what it was flagged as after the 2nd failed attempt:
  no available tool exposes what a Routine-fired session's transcript
  actually does step by step, so root-causing past this point needs
  either a fundamentally different diagnostic (not another prompt
  variant) or accepting the unattended loop isn't fixable with tools
  currently available and relying on interactive sessions instead.
  **Do not fire this Routine again without one of those two.**
  **CLOSED 2026-08-25: asked Het directly -- keep spending on more
  attempts, or accept manual/interactive check-ins?** He chose manual
  check-ins. This is not marked FIXED (it isn't) -- it's a deliberate,
  informed decision to stop investing further debug time/money into
  unattended operation and rely on interactive sessions + the (working)
  daily report Routine instead. Reopen only if a genuinely new diagnostic
  capability becomes available (e.g. real transcript visibility into a
  Routine-fired session), not on a hunch.

- **FIXED (merged to main) | 2026-08-25 | nifty-benchmark-missing-from-live-ledger** — while
  checking whether the agents were actually trading (real question from
  Het), read the actual production `factory_state/ledger.json` on `main`
  and found `nifty_benchmark` absent from the registry, despite P0-3
  merging in PR #1. Root cause: `load_state()` only calls
  `seed_registry()` when a ledger doesn't exist yet -- an existing ledger
  never picks up new seed entries added afterward. Fixed `load_state()` to
  backfill any missing seed_registry() key additively (new contestant,
  existing ones untouched). Tested against the exact real scenario.
  Commit `c449bff` on the feature branch, merged to main via PR #2
  (`b55b562`) with Het's fresh explicit confirmation. Takes effect on the
  next scheduled `factory.yml` run against main's ledger.json.

## FIXED

- **FIXED (on branch, not yet merged) | 2026-08-26 | health-check-stale-local-false-positive**
  — `tools/health_check.py` run against a plain local checkout reliably
  reported a "registry drift" warning that wasn't real on `main` --
  because the local checkout tracks the WORKING BRANCH, but
  `ledger.json` is only ever auto-committed by `factory.yml` to `main`,
  never the branch. Every Routine prompt already said "fetch fresh,
  don't trust a stale copy" in English each firing; nothing enforced it
  in code, so it kept getting silently skipped (including by this
  session, more than once today). Fixed by adding a `--live` flag
  (`health_check.py`) and a `live=` param (`healer.report()`) that fetch
  `ledger.json` fresh from `main`'s raw GitHub content instead of
  reading the local file. Verified: `--live` shows clean against real
  main data (which already has the keys); plain local mode still
  correctly flags the genuinely-stale local copy, proving the flag does
  real work. Commit `963c466`. Not yet merged -- needs Het's review, per
  the bounded-programming rule (draft+test on branch, never self-merge).
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
