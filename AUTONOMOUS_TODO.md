# STRATEGY FACTORY — AUTONOMOUS TODO

This file is the persistent memory, roadmap, task queue, and handoff
document for autonomous Claude Code development on this repo. Read it
FIRST at the start of every session. Update it BEFORE ending every
session. Do not rely on conversation history as the only source of
continuity — a fresh session with zero prior context must be able to
pick up from this file plus `git log`/`git status` alone.

**Where this lives right now:** this file, and all the work it
describes, is on branch `claude/scheduled-maintenance-template-d7yufr`
(PR #1, open, unmerged) — NOT on `main` yet. If you're starting a fresh
session on `main` and don't see this file, check that branch / PR #1
before assuming no work has happened.

## Current Objective

Per `01_objectives.txt`: prove, at near-zero cost, whether a real
trading edge exists in Indian equities (NSE) before risking capital —
build an evidence machine, not a money machine. Run many independent
strategy hypotheses in parallel (a tournament). Fund only what earns it
through a fixed mechanical promotion ladder. Keep downside capped
(paper trading = Rs 0, first real rung = Rs 10,000).

The Three Laws (binding, from `01_objectives.txt` / `CLAUDE.md`-equivalent):
1. Hypotheses are written before testing — never mined from data.
2. Live strategies are never mutated — only replaced via bred children
   that start over at rung 0.
3. Capital is earned through the ladder, never granted.

**Two explicit, authorized deviations exist** (see Decisions Made below)
— the advisor layer built this session deliberately overrides Law 1 and,
behaviorally, Law 2, with mitigations. Any future session extending the
advisor layer should read that decision in full before changing it.

## Current Phase

Phase 2: Advisor-informed evolution layer built and self-reviewed, sitting
in an open, unmerged PR (#1). Not yet merged to `main` — Het has twice
explicitly deferred merging (see Decisions Made). No monthly training
workflow has run against real data yet (Yahoo Finance is also unreachable
from this sandbox, so no session so far has run it against real prices at
all — everything is synthetic-data-tested).

## Active Task

None in progress — the Sharpe-guard fix below was picked up and completed
this session. Next session should pick the highest-priority item from the
queue below.

## Priority Queue

### P0 — Critical
*(none currently open)*

### P1 — High
- [ ] **Get PR #1 reviewed and merged (or explicitly rejected) by Het.**
      Everything below is stalled behind this — the advisor layer,
      dashboard changes, and this TODO file itself only exist on the PR
      branch. This is a decision-gate item, not something to do
      autonomously (merging main requires explicit authorization — see
      Git Safety Rules).
- [ ] Confirm `dashboard.py`'s raw-GitHub-URL auth actually works for a
      real, non-Claude-environment visitor (item 2 from
      `03_learnings_and_suggestions.txt`, still open) before any
      Streamlit Cloud deployment. **Investigated this session, but
      INCONCLUSIVE from this sandbox — do not treat as resolved.** A
      direct `curl` (unauthenticated) to the raw ledger URL returned
      HTTP 200 with real content, which looked like a resolution — but
      the response headers plus `env | grep -i proxy` showed
      `GH_TOKEN=proxy-injected`: every session in this environment has
      its outbound GitHub requests transparently authenticated by the
      sandbox's own proxy, Claude-Code-on-the-web session or not. That
      means this sandbox categorically cannot distinguish "the repo is
      public" from "the repo is private but I'm silently authenticated."
      The only real test is external to this environment: open the raw
      ledger URL (`https://raw.githubusercontent.com/Hetlife/strategy-
      factory/refs/heads/main/factory_state/ledger.json`) in a plain
      browser private/incognito window with no GitHub login. A future
      session should ask Het to do this once, or find another way to
      probe repo visibility that isn't routed through this proxy (e.g.
      GitHub's own API might expose `private:` on the repo object if a
      session's token scope allows reading it — worth trying
      `get_file_contents`/repo-metadata tools before assuming another
      curl will help, since any such tool call goes through the same
      proxy).
- [ ] Once PR #1 merges: let `.github/workflows/advisor_training.yml` run
      at least once against real data (scheduled or manual dispatch), and
      verify `parameter_bank.json` looks sane against real market data
      (everything tested so far is synthetic).

### P2 — Medium
- [x] ~~Decide the `spawn_children()` coverage gap~~ — **done, commit
      `4a69110`**. Treated as a completeness gap (the seed grid only ever
      had one `input_cost` instance, so no breeding rule had been written
      for it) rather than a values decision: extended `spawn_children()`
      with the same mechanism-bounded neighbour-variant pattern the other
      families use. `monsoon` deliberately still excluded — dormant no-op
      with no CSV, breeding it would be pointless until real rainfall
      data exists (tracked below).
- [ ] Small, safe performance work (item 3): vectorize the per-contestant
      loop in `update()`/`report()`, `yf.download(..., threads=True)`.
      Must not change any strategy's signal logic or promotion math.
      Explicitly deferred in the original suggestions list until other
      signals show results — low urgency at ~20-40 contestants.
- [ ] `train_brain.py` is now fully superseded by `advisors.py` (same
      backtest-and-rank idea, but `advisors.py` is actually wired into
      `report()`, uses 3 independent heuristics instead of one grid-search
      winner, and doesn't have the known typo). Decide: delete
      `train_brain.py`, or leave it as disconnected research. **Done,
      commit `85cd1a5` — removed.** Fully reversible via git history if
      the offline-research angle is wanted back later.
- [ ] No monsoon CSV has been sourced yet — `sig_monsoon` is a dormant
      no-op. Low priority per the original suggestions list.

### P3 — Future
- [ ] Broker/execution/API-key integration — explicitly NOT to be started
      until at least one real promotion has happened under current rules
      (see `03_learnings_and_suggestions.txt` item 6). Do not touch.
- [ ] Options/futures/leverage/margin logic of any kind — permanently out
      of scope per Law 1/objectives, not just deferred.
- [ ] Review `RULES` thresholds (Sharpe 0.4, 126 days, etc.) — only after
      3-6 months of real paper-trading history, and any argument for
      changing them must be written down BEFORE looking at how it would
      affect current contestants' verdicts (avoid hindsight bias). Do not
      touch `RULES`/`LADDER`/`COST_PER_SIDE` without Het's explicit,
      separate instruction — these are financial risk parameters, not
      code-quality parameters.

## Completed

- **2026-08-23, commit `0948c8d`** — Verified the Sunday weekly `report()`
  step actually fires (the cron-condition bug from `b003af3` is confirmed
  fixed in production, not just in the YAML) by diffing real
  `ledger.json` history across three Sunday runs. No code change; findings
  in `maintenance_notes/2026-08-23_status_note.md`.
- **2026-08-23, commit `00f5651`** — Built the advisor-informed evolution
  layer: `advisors.py` (monthly historical backtest + 3-heuristic
  ensemble scoring), evolution logic in `factory.py`'s `report()`
  (paper-tier, outside-top-10 contestants get retired and replaced with
  advisor-blended children), self-tuning `trust_weight`
  (`factory_state/advisor_state.json`), monthly training workflow
  (`.github/workflows/advisor_training.yml`), and dashboard updates
  (Lineage column, Advisor Layer section). Explicitly overrides Law 1 and
  Law 2 — see Decisions Made. Full rationale in
  `maintenance_notes/2026-08-23_advisor_layer.md`.
- **2026-08-23, commit `4a31a0e`** — Self-review pass found and fixed 3
  real bugs: `cost_efficiency_advisor` was measuring per-day, not
  per-round-trip, cost efficiency; `backtest()` silently swallowed
  strategy-function exceptions; a paper-tier contestant reset on a
  non-terminal demote wiped its `lineage` before it could ever be
  trust-scored.
- **2026-08-23, commit `2635bcf`** — Dashboard readability: parameter-bank
  `Params` column now renders as `key=value` pairs instead of a raw
  truncated dict repr; cost-efficiency column labeled with its unit.
- **2026-08-23, commit `5669fb0`** — Fixed a pre-existing Sharpe
  correctness bug in `report()`: variance floored at `1e-12` could
  produce absurd Sharpe values (seen: ~106,512) with few `days_in_market`,
  which could satisfy `min_sharpe` on essentially no evidence and cause a
  false PROMOTE. Now returns `NaN` below `MIN_SHARPE_SAMPLE_DAYS=20`
  (mirrors `advisors.py`'s own guard); `RULES["min_sharpe"]` itself is
  untouched. Verified this actually prevented false PROMOTEs in the same
  synthetic scenario that exposed the bug.
- Also this session: built a standalone local-preview Artifact (dark
  trading-terminal styling, inline-SVG charts, no external deps) so the
  new dashboard sections could be inspected before any push — still live
  at the URL Het was given; not part of the repo.
- **2026-08-24, commit `4a69110`** — Extended `spawn_children()` to breed
  `input_cost` strategies (neighbour-variant `lb`/`drop`, same
  mechanism-bounded pattern as the other families). `monsoon` still
  deliberately excluded. Resolves the P2 coverage-gap question from
  `03_learnings_and_suggestions.txt`.
- **2026-08-24, commit `85cd1a5`** — Removed `train_brain.py`, fully
  superseded by `advisors.py`. Resolves the other P2 open question from
  `03_learnings_and_suggestions.txt` (its own suggested resolution was
  "fix it... or remove it"). No references anywhere else in the repo;
  reversible via git history.

## Deferred

- Broker/execution integration, options/futures/leverage — see P3 above,
  not deferred-until-later so much as out of scope until explicit
  conditions are met.
- Merging PR #1 — Het was asked directly twice this session; first said
  "yes, merge it," then an ambiguous "let's start again darling" arrived
  mid-merge-prep, so I re-asked rather than guess, and the final answer
  was **hold off**. Do not merge without a fresh, unambiguous
  confirmation in a future session — don't treat the earlier "yes" as
  still standing.

## Known Bugs

*(none currently open — the Sharpe variance-floor bug above was the only
one identified and it's fixed as of commit `5669fb0`)*

## Technical Debt

- `train_brain.py` is dead code, fully superseded by `advisors.py` (see
  P2 queue item above). Not urgent, but leaving two backtest-and-rank
  scripts in the repo invites future confusion about which one is live.
- All advisor-layer testing so far is against **synthetic** random-walk
  price data — Yahoo Finance has been unreachable from every sandbox this
  project has run in so far this session. Nothing in `advisors.py` or the
  evolution path in `report()` has been validated against real market
  data yet. This is the single biggest open risk on the new code — a
  future session (or the GitHub Actions runner, which does have real
  network access) should run it for real and sanity-check the output the
  first chance it gets.

## Ideas / Future Improvements

- Dashboard: a "market regime" indicator, correlation matrix across live
  contestants, and an "upcoming autonomous actions" preview (what
  evolution/promotion decisions the *next* `report()` run would make
  given current state) would all fit the existing Advisor Layer section
  well. Not started — ranked below the P1/P2 queue above.
- Advisor layer: currently only blends numeric hyperparameters
  (threshold/hold/lookback/lb/drop); it never proposes switching a
  sector's leader ticker or trying a different strategy family for an
  underperformer. Could be a real capability gain, but widens the
  mutation space significantly — would need its own Law-1/Law-2
  discussion with Het before building, same as the current advisor layer
  did.

## Current Architecture Notes

See `02_architecture.txt` for the pre-advisor-layer baseline (still
accurate for everything it describes). Advisor-layer additions on top of
that baseline:
- `advisors.py` — new file, monthly training script, not wired into the
  daily/weekly cron in `factory.yml` (has its own `advisor_training.yml`).
- `factory.py` — `blank_stats()` gained `lineage`/`evolved_out`/
  `trust_scored` fields (backfilled onto old entries by `load_state()`);
  `report()` gained the evolution step and the Sharpe NaN-guard.
- New state files: `factory_state/parameter_bank.json` (written by
  `advisors.py`, read by `report()` and `dashboard.py`),
  `factory_state/advisor_state.json` (read/written by `report()`, read by
  `dashboard.py`). Neither exists on `main` yet — only on the PR branch,
  and `parameter_bank.json` doesn't exist anywhere yet since no training
  run has happened against real data.
- `dashboard.py` — new "Advisor Layer" section + `Lineage` leaderboard
  column, both degrade gracefully (show an empty/waiting state) when the
  new state files don't exist yet.

## Decisions Made

- **Law 1 override (advisor layer trains on historical price data):**
  explicitly requested and authorized by Het after being shown the
  tradeoff directly (a Q&A comparing "train on own live track record"
  vs. "train on raw historical price data" — Het chose the latter).
  Mitigation kept: parameter grids stay inside the same mechanism-bounded
  ranges the seed registry already uses; one of the three advisor
  heuristics specifically scores regime-robustness.
- **Law 2 override (evolution replaces underperformers):** explicitly
  requested by Het ("we want them to be mutated..."). Mitigation *I*
  chose, not asked again: mechanically still only ever creates a new
  registry key (never edits one in place), and is restricted to
  paper-tier (rung 0) contestants only — anything already on a
  real-money rung is excluded from this path entirely and still only
  evolves via the pre-existing `spawn_children()` breeding-on-promotion
  mechanism. Flagged explicitly to Het rather than silently assumed.
- **PR #1 merge:** asked directly twice this session. Current standing
  answer is **hold off, do not merge**. Treat this as the live decision
  until a future session gets an unambiguous fresh confirmation.
- **Branch discipline:** all work stays on
  `claude/scheduled-maintenance-template-d7yufr` / PR #1. Never push
  directly to `main`, never merge without explicit per-session
  confirmation (a prior session's "yes" does not carry forward).

## Tests Performed

All tests this session (and the prior advisor-layer session) ran against
**synthetic random-walk price data**, monkeypatching
`fetch_prices()`/`fetch_history()` — Yahoo Finance is unreachable from
this sandbox's network policy, which would block the *unmodified*
`factory.py` too. Nothing has been run against real market data.

- `update()`/`report()` end-to-end, ~20 cycles: no crashes, sane verdicts.
- `advisors.py train()` against synthetic history: valid 7-bucket bank.
- Forced evolution-eligible state, re-ran `report()`: correct lineage
  bookkeeping, correct paper-tier-only restriction.
- Re-ran full suite after each bug-fix commit: no regressions.
- ~4-year-equivalent long synthetic simulation: multi-generation lineage,
  a real promotion with normal breeding alongside advisor evolution, a
  6-point trust-weight history.
- `dashboard.py` launched locally via `streamlit run`, loaded in real
  headless-Chromium (Playwright) twice: once against real GitHub `main`
  data (confirmed graceful empty states for not-yet-existing advisor
  files), once against the long-simulation demo data via a local file
  server (confirmed all new UI renders correctly with populated data).
- This session's Sharpe-guard fix: confirmed the same forced-evolution
  scenario that previously produced absurd Sharpe values and false
  PROMOTE verdicts now correctly shows `NaN`/`hold` instead.
- **INVESTIGATED, INCONCLUSIVE** (not a pass): `dashboard.py`'s raw-URL
  auth. A direct `curl` from this sandbox to the raw ledger URL returned
  200 unauthenticated, which looked like a clean pass — until checking
  `env | grep -i proxy` showed `GH_TOKEN=proxy-injected`, meaning this
  sandbox transparently authenticates all outbound GitHub requests.
  The 200 proves nothing about what a real anonymous visitor would see.
  See the P1 queue item above for the actual test needed.

## Last Session Handoff

### What was completed
Created this file. Fixed the Sharpe variance-floor correctness bug in
`report()` (commit `5669fb0`) — verified it actually prevents the false
PROMOTE verdicts it was causing. Investigated `dashboard.py`'s raw-URL
auth question (P1) and found the investigation itself was flawed — see
Problems Encountered — so it's still open, just better understood now.
Extended `spawn_children()` to breed `input_cost` (commit `4a69110`) and
removed the now-superseded `train_brain.py` (commit `85cd1a5`), resolving
both P2 open questions from `03_learnings_and_suggestions.txt`.

### What was not completed
`dashboard.py`'s private-repo-auth question is still genuinely open —
see the P1 queue item for exactly what test is still needed and why this
sandbox can't perform it. The P1 queue item "get PR #1 reviewed and
merged" is explicitly NOT something to do autonomously — it needs Het's
decision, not more code. Remaining P2 items (vectorization, monsoon CSV
sourcing) are untouched.

### Exact point to continue from
Pick the next item from the Priority Queue above. The private-repo-auth
question needs either Het to run one manual browser check, or a future
session to find a way to probe it that doesn't route through this
sandbox's GitHub-authenticating proxy — don't re-attempt it with a plain
`curl`/`requests` call from inside this environment, that exact mistake
is documented below. Otherwise, the vectorization item (P2) is the last
unstarted, non-decision-gated item on the queue — low urgency at current
contestant counts, a reasonable pick only once everything above it is
exhausted.

### Files changed this session
`AUTONOMOUS_TODO.md` (new), `factory.py` (Sharpe guard fix +
spawn_children input_cost breeding), `train_brain.py` (deleted).

### Tests run
See "Tests Performed" above — synthetic-data suite re-run after each
fix, all passing; direct unit-style calls to `spawn_children()` with
input_cost params confirmed correct bounded children and a correctly
excluded out-of-range edge case; false-promotion scenario confirmed
fixed.

### Problems encountered
Same standing limitation as before: no real-market-data testing possible
in this sandbox (network policy blocks Yahoo Finance). New this session:
attempted to settle the private-repo-auth question with a direct `curl`
to the raw ledger URL from this sandbox; it returned 200 and looked
conclusive, but turned out to be a false positive — this sandbox's
outbound proxy injects a GitHub token (`GH_TOKEN=proxy-injected`) into
every GitHub request regardless of the target repo's real visibility, so
the test proved nothing. Caught this before writing it up as resolved.
Any future attempt to test this from inside a Claude Code session in
this kind of environment will hit the same wall.

### Recommended next action
Either: (a) get Het's explicit decision on PR #1 (merge / keep open /
close), which unblocks everything else, or (b) if continuing
autonomously without that decision, pick up the `dashboard.py`
private-repo-auth verification (P1) since it's independently useful and
not blocked by the merge decision.

## Autonomous Development Rules

- Never lose previous progress. Read this file and `git log` before
  assuming any prior session's state.
- Never delete unfinished tasks without documenting why (move to
  Deferred with a reason, don't just delete).
- Never mark a task complete without verification (a test run, a
  screenshot, an actual diff — not "the code looks right").
- Always leave a clear handoff for the next session before stopping.
- Never touch `RULES`, `LADDER`, or `COST_PER_SIDE` without Het's
  explicit, separate instruction in that session.
- Never mutate an existing `registry` entry for a strategy with
  contestant history — new ideas are new registry keys.
- Never add a strategy whose parameters were chosen by scanning
  historical data *without* a stated real-world mechanism first — this
  applies to anything outside the already-authorized advisor layer.
- Never add options/futures/margin/leverage logic.
- Never add or modify broker/execution/API-key code.
- Never push directly to `main`, never merge a PR, without explicit
  per-session authorization from Het.
