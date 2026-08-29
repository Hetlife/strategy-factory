# PROJECT STUDY — the full story, for any future AI session

**What this file is:** a single, comprehensive, chronologically-and-
thematically organized reference covering everything this project has
done, why, and what it means — written so a future session (any model,
any token budget) can get properly oriented without re-reading dozens
of commit messages. It is a *study* document — narrative, explanatory,
meant to be read when you need to understand the whole arc, not just
the next task.

**This is not a replacement for anything else:**
- `CLAUDE.md` — binding rules, read every session, wins over this file
  if they ever disagree.
- `GOALS.md` — the north star, one page, read after `state.json`.
- `EXECUTION_PLAN.md` — condensed rules/gates/mechanics reference.
- `.autonomous/state.json` — live structured state, read first, always.
- `AUTONOMOUS_LOG.md` — terse one-line-per-action append-only log, the
  primary source this file was synthesized from.
- `.autonomous/RUNBOOKS.md` — mechanical step-by-step procedures for a
  lower-token-budget session. Companion to this file: this explains
  *why* and *what happened*; RUNBOOKS.md tells you *exactly what to do
  right now*.
- `.autonomous/bug_log.md` — defects found/fixed, append-only.
- `.autonomous/het_directives.md` — Het's own requests over time +
  standing NEEDS HET section.

Read this file when: you're new to the project and want the real
story, not just rules; you're about to make a judgment call and want
precedent; someone (including Het) asks "why does it work this way";
or you want to understand a past decision before extending it.

---

## PART 1 — WHAT THIS ACTUALLY IS

Strategy Factory is a self-evolving tournament of paper-traded
strategies for Indian equities (NSE), built for Het (SevaaConnect
Solutions Pvt Ltd, Surat, India). It runs entirely on free
infrastructure (GitHub Actions, Rs 0/month) and is operated day to day
by AI sessions like this one — Het is intentionally hands-off on
implementation.

**The one-sentence goal (GOALS.md):** find out, honestly and
rigorously, whether Het's domain knowledge (construction/cement/
infra/steel) produces a real, tradeable edge in Indian equities — and
if it does, grow a small amount of capital into a large one over years,
patiently, without ever lying to ourselves about the evidence.

### This is an evidence machine, not a money machine

This is the single most important framing in the entire project, and
it gets tested repeatedly — Het periodically asks (in different words)
for things that would trade the evidence-machine framing for a
money-machine one: leverage, F&O, an AI that controls real capital,
mutating live strategies to look better, merging without confirmation
"to save time." Every one of these has come up at least once and been
declined or deliberately bounded. See Part 4.

**What "done" looks like, in Het's own words (2026-08-24, via direct
Q&A — see `operator_profile.md`):** not primarily profit. Success is
*Het becoming someone who can build and reason about a system like
this* — understanding why it works or doesn't, not trusting a black
box. He is explicitly, on record, comfortable with a 12-month wait and
with "no edge found, buy an index instead" as a fully legitimate,
successful outcome. Don't re-derive this, don't assume it's changed
without him saying so directly and explicitly.

### The Three Laws (binding, never violated without fresh explicit authorization)

1. Hypotheses are written before testing — never mined from data.
2. Live strategies are never mutated — only replaced via bred children
   that start over at rung 0.
3. Capital is earned through the ladder, never granted.

Two standing, explicitly authorized exceptions exist (both logged in
`AUTONOMOUS_TODO.md`'s Decisions Made, not to be re-derived or
re-litigated):
- The advisor layer (`advisors.py`) trains on historical price data —
  a Law 1 override, authorized after Het was shown the tradeoff
  directly.
- `report()`'s evolution step replaces paper-tier (rung 0) stragglers
  — a Law 2 override, but mechanically still only ever creates a new
  registry key, never touches a real-money-rung contestant.

### The timeline, honestly stated

| Milestone | Timing | What it tells us |
|---|---|---|
| Phase 0 complete | 2026-08-24 (done) | The measuring stick is honest. Nothing about whether an edge exists. |
| Phase 1 minimum evidence window | 12 months from Phase 0 (~mid/late 2027) | Whether ANY strategy clears the bar AND beats Nifty net of real cost+tax. Could be yes or no. |
| Phase 2 (first real capital) | No fixed date, contingent on Phase 1 | Whether live results match paper predictions over 6 more months. |
| Phase 3/4 | Years out | Only relevant if everything before worked. |

The single most likely outcome, stated plainly: most systematic retail
trading attempts do not find a durable edge. SEBI's own study found
~93% of individual F&O traders lost money FY22-24 (different asset
class, cited only as calibration for how hard this generally is).
"No edge found" should be treated as a live possibility all the way
through Phase 1, not a remote one.

---

## PART 2 — ARCHITECTURE, AS IT ACTUALLY STANDS

- **`factory.py`** — the core engine. `update()` runs daily (realizes
  P&L, no-lookahead ordering verified correct). `report()` runs weekly
  (Sharpe/drawdown/PROMOTE/DEMOTE verdicts, evolution). State lives in
  `factory_state/ledger.json`, never hand-edited.
- **`advisors.py`** — monthly training script. Backtests a
  mechanism-bounded parameter grid through the same `sig_*` functions
  `factory.py` runs live, scores with 3 heuristics, writes
  `factory_state/parameter_bank.json`. First real run: 2026-08-27.
- **`dashboard.py`** — Streamlit, read-only, sourced from GitHub raw
  URLs. Never a write path. Hosted by Het himself on Streamlit
  Community Cloud (confirmed public/fine — paper data only, Rs 0 real
  risk).
- **The Trading Floor Artifact** — a separate, mobile-first published
  Claude Artifact (pixel/terminal-themed), built because Het wanted to
  "see it right now" on his iPhone without a laptop/server. Has its
  own note-bowl channel for Het to write back to Claude (the actual
  "notebook" the confidence-threshold rule refers to — not a new thing
  to build). URL: `https://claude.ai/code/artifact/6af2bce8-b4a5-4b08-
  b60a-916c239e8a65`. Auto-generated from real data via
  `tools/build_trading_floor_state.py`.
- **`agents/` team** — 8 read-only/advisory agents (Judge, Researcher,
  Breeder, Risk Manager, Reporter, Healer, HR, Master Trader). None
  write to `ledger.json`. None decide anything `factory.py`/
  `advisors.py` haven't already decided. Each has its own
  `workspace.md` scratch file (never read by any `sig_*` function).
- **`.github/workflows/`** — `factory.yml` (daily update + Sunday
  report, commits to main), `supervisor.yml` (free, 15-min cadence,
  detection-only, no commits), `advisor_training.yml` (monthly),
  `diagnose_event_thresholds.yml` / `diagnose_nifty100_tickers.yml`
  (manual-dispatch, read-only diagnostics — this pattern exists
  because GitHub Actions runners have real internet access and this
  sandbox does not).
- **`tools/health_check.py` / `tools/supervisor_check.py`** —
  deterministic, pure-Python monitors. `--live` flag fetches
  `ledger.json` fresh from `main`'s raw GitHub content instead of a
  local checkout, which only ever has a stale copy (see Part 5's bug
  history — this bit twice).

---

## PART 3 — THE FULL STORY, CHRONOLOGICALLY BY THEME

### Phase 0 buildout (2026-08-23 to 2026-08-24)

Four gating deliverables, all shipped and tested before any further
feature work: a size-aware cost model (`round_trip_cost()` replacing a
flat `COST_PER_SIDE` that understated real cost by up to 3x at small
position sizes — a real, live-money-relevant bug, fixed before it
mattered), a post-tax expectancy metric (STCG/LTCG-aware, ranking
context only, never feeds the PROMOTE/DEMOTE verdict), a permanent
Nifty buy-and-hold benchmark contestant (the bar everything else has
to clear, immune to demotion/retirement/evolution), and committed
falsification criteria (`EXECUTION_PLAN.md` Section 5 — six specific
kill conditions, written down before more data could bias them).
Alongside this: the advisor layer (Law 1 override, explicitly
authorized) and the `agents/` team architecture were built. Phase 0
gate cleared 2026-08-24 — `current_phase` flipped to `phase_1` in
`state.json`.

### The autonomous dev-loop saga (2026-08-24 to 2026-08-25) — a real, resolved failure

An unattended Routine meant to do continuous background development
work fired **five separate times**, each running real minutes with
real token spend, each ending cleanly (not crashed) — and each
producing **zero commits**. This was investigated seriously, not
hand-waved: two structurally different fix attempts were tried
(explicit retry-on-classifier-timeout instructions, then an
explicit-clone-first protocol), both independently verified via
`list_commits` with session attribution, both failed the same way. The
likely proximate cause (`create_trigger`-fired sessions don't carry the
same repo-binding `create_session` sessions do) was identified but
never fully proven, because no tool exposed the Routine session's own
internal transcript. Rather than keep spending money on blind
prompt-wording guesses, Het was asked directly: keep debugging, or
accept manual/interactive check-ins? **He chose manual check-ins.** The
Routine is disabled, not deleted, logged in `bug_log.md` as CLOSED
(accepted, not fixed) — distinct from FIXED. **Do not re-enable it
without an actual new diagnostic capability, not another prompt
tweak.** This is the single most expensive lesson in the project's
history and the reason the current operating model is: an hourly
check-in Routine (the tightest interval the platform allows — 15-min
was tried and rejected by the platform itself) plus a free, 15-min
GitHub Actions supervisor for cheap, code-only detection in between.

### Monitoring evolution — health_check.py, the --live bug (twice), and the IT-guy protocol

Built `tools/health_check.py` (deterministic, pure-Python: registry
drift vs `seed_registry()`, `state.json` well-formedness, `CLAUDE.md`
hash drift, `bug_log.md`/`state.json` contradictions) after Het asked
to shift repeated manual reasoning into code. It immediately caught two
real, previously-unnoticed bugs. Then `tools/supervisor_check.py` +
`.github/workflows/supervisor.yml` gave free, 15-min-cadence detection
with zero Claude session cost (a real cost tradeoff was flagged to Het
first — a paid session firing every 10-15 min would have been a ~50x
jump in cost for no more real information, since the underlying data
only changes once/day; he chose the free code-only option). **The same
bug class hit twice**: a plain local checkout only ever has the
*branch's* `ledger.json`, but `ledger.json` is only ever auto-committed
to `main` — so a naive local read is always stale and produces false
positives. First caught in `health_check.py` (2026-08-26), fixed with a
`--live` flag. Then caught *again*, at higher severity, in
`supervisor_check.py` (2026-08-29) — that check's headline "the daily
run may have stopped firing" alarm was firing FALSELY while the daily
run was completely healthy. Same fix pattern (`--live`, fetch fresh
from `main`), same lesson: **always use `--live`, no exceptions.** The
"IT guy protocol" (`.autonomous/it_guy_protocol.md`) formalizes the
honest, zero-extra-cost version of "an agent that fixes bugs and
improves things": event-driven only, checks `supervisor.yml`'s run
history as part of normal Routine firings, proposes fixes on the
branch, never auto-merges.

### The dashboard's evolution — from static numbers to a real portfolio view

`dashboard.py` went through several real redesigns, each driven by
specific Het feedback, each tested via headless browser against real
live GitHub data before being called done: an "Office" tab (agent desk
cards), a factor-rating toggle, a heartbeat banner (later replaced by
a portfolio-style hero card — total paper P&L, capital at play,
vs-benchmark comparison, with a persistent "PAPER / real capital
invested: Rs 0" badge so it can never be misread as real earnings), a
top-performer stat replacing a static "Rs 100,000" display Het
correctly flagged as meaningless, and a declutter pass removing
duplicate metrics. One real bug found and fixed here: a note Het saved
via the dashboard's local Notes box appeared to save successfully but
was written to the *hosted container's own throwaway disk*, never
committed to git — invisible to any Claude session, no warning given.
Fixed with an explicit warning pointing to the Trading Floor Artifact's
note bowl as the channel that actually reaches Claude.

### Adding new strategy contestants — the established, repeatable pattern

Several new contestants were added over the project's life, each
following the same shape, which is now the template for any future
one (see `RUNBOOKS.md` RUNBOOK 7 for the mechanical version):
1. **State the mechanism first**, in a code comment, before the
   contestant sees a single day of live evidence (Law 1).
2. **Reuse an existing `sig_*` function** where the underlying
   mechanism is the same and only the parameters/universe differ
   (crude-oil input-cost hypotheses reused `sig_input_cost`; the Nifty
   100 momentum contestant reused `sig_momentum`) — a genuinely new
   signal function is a much higher bar than a new registry entry.
2026-08-29's Nifty 100 momentum contestant (`mom_nifty100_lb90`) is
the fullest example of this pattern executed end-to-end: mechanism
(cross-sectional momentum, Jegadeesh & Titman 1993 + NSE-focused
replications) stated before any evidence; reused `sig_momentum`
unchanged; a new `UNIVERSE["nifty100"]` basket built from training
knowledge (this sandbox cannot reach nseindia.com/wikipedia.org/
smallcase.com — confirmed via real attempted `WebFetch` calls, same
restriction class as the documented Yahoo Finance block); then
**actually verified for real**, not left as a flagged assumption — a
manual-dispatch diagnostic workflow (`diagnose_nifty100_tickers.py`)
ran on GitHub Actions (which has real network access) and found 2 of
95 tickers (`TATAMOTORS.NS`, `LTIM.NS`) returning a genuine HTTP 404,
likely from a 2025 corporate-action ticker change rather than
delisting. Both were removed rather than guessing a replacement. This
"verify the assumption for real via GitHub Actions instead of leaving
it as a human TODO" pattern is now the standard for any claim this
sandbox can't directly check.
3. **Test with a synthetic regression** (40-cycle `update()` + `
   report()` against monkeypatched price data) before ever committing
   — "it imports without error" is never treated as a test.
4. **New registry key only** — never mutate an existing one (Law 2).
   The event_drift threshold recalibration (2026-08-28) is the
   clearest example of this discipline: rather than adjust the original
   9 thresholds (which would corrupt ~38 days of already-collected
   evidence on live contestants), 3 *additional* variants were added
   at each leader's real, measured 85th percentile of daily returns —
   the originals stay byte-identical.

### Declined or bounded requests — the recurring pattern worth understanding

Het periodically asks for things that would cross a Hard Rule or the
evidence-machine framing. Every one of these was taken seriously, not
dismissed, and either declined with reasoning or built as a
deliberately bounded/safe version. See Part 4 for the full list — this
is the single most important pattern to recognize if a future ask
rhymes with one of these.

### The efficiency pass (2026-08-29)

Het asked to "make the program more efficient." Profiled *before*
guessing: `update()` itself is 32ms for 26 contestants — genuinely
fast, so the queued "vectorize the loop" idea would have optimized
~0.2% of a job's real time. The actual cost was dependency
reinstallation: "Install dependencies" was 65-79% of total job time on
every single run. Added pip wheel caching to all 4 workflows. The
first commit message estimated ~9 hrs/month saved by assuming the
whole install step would vanish; the measured real result (cold vs
warm cache, real dispatches) was ~3s/run saved, corrected down to
~2.4 hrs/month — a real, self-caught, self-corrected overstatement,
logged as a correction rather than left standing.

---

## PART 4 — DECLINED OR BOUNDED REQUESTS, AND WHY (read this before repeating one)

| What was asked | What happened | Why |
|---|---|---|
| An AI "master trader" that receives real money and distributes it across strategies | Declined entirely. Built the safe version instead: `agents/master_trader/master_trader.py`, same read-only/advisory tier as every other agent, zero write access to `ledger.json`/`RULES`/`LADDER`/`COST_PER_SIDE`, never merges. `recommend()` only synthesizes existing agents' output. | Direct violation of Law 3 (capital earned through the ladder, never granted) and EXECUTION_PLAN.md Section 5f's kill condition. |
| A Master Trader that adjusts `RULES`, sets risk parameters/position sizing, and approves its own merges — asked for **even under "I'm getting on a flight, take all the permission you want"** | Declined explicitly, even under time pressure. | This is precisely the failure mode the fresh-confirmation-every-time rule exists to prevent — granting broad authority under time pressure is the exact scenario it's designed against. |
| Options/futures/leverage, "as a new class so we can make maximum profit" | Declined, logged for a dedicated future conversation. | Named hard rule. GOALS.md's own SEBI citation (~93% of F&O traders lose money) is for the exact asset class requested. Leverage would multiply an edge that hasn't been demonstrated at all (day ~40 of 126, Rs 0 deployed, zero promotions). Unlike cash equity, F&O can lose more than capital committed. |
| A gold-price input-cost hypothesis | Declined — asked Het directly, he chose skip. | No comparably direct mechanism to cement/infra/steel was found; best candidate was a weak two-hop "gold as rupee-weakness proxy" story. Crude oil was added instead because kilns/furnaces are directly energy-intensive — a real, one-hop mechanism. |
| "Give you every permission" (2026-08-24, and again 2026-08-29 as "every permission... to reach the goal of making consistent large profit") | Neither treated as removing the fresh-confirmation-per-merge rule or the Hard Rules. Docs/tooling/new-registry-key work proceeded; guardrails stayed unconditional. | CLAUDE.md states this exact scenario by name — a cost-axis grant is not a risk-axis grant, and a blanket "permission" grant has already happened once before with guardrails explicitly unchanged. |
| Live monsoon data activation from a stale (2017) historical CSV | Declined to wire it into the live signal path, even though the historical data was genuinely sourced. | Forward-filling a 9-year-stale "current" reading and trading on it would be *worse* than staying dormant — it would look active while silently being wrong. `monsoon_cement` stays dormant until a genuinely current feed exists. |
| Training multiple copies of agents on identical historical data, faster/more often, to "learn faster" | Explained directly rather than built: identical copies on identical data produce identical results, not more evidence. The real bottleneck (one new real trading day per calendar day) cannot be sped up by running more often. | This is the recurring "make it trade faster" question in different phrasings — the answer is always the same: the evidence clock runs on calendar days, not compute cycles. The one legitimate acceleration already exists: `advisors.py`'s bounded monthly parameter-grid backtest against real historical data (Law 1 override, already authorized, already running for real since 2026-08-27). |

---

## PART 5 — REAL BUGS FOUND AND FIXED (condensed; full detail in `bug_log.md`)

- **Cost model understated real transaction cost by up to 3x** at
  small position sizes (flat `COST_PER_SIDE` missing the fixed DP
  charge component). Fixed as part of Phase 0 (P0-1).
- **Sharpe could blow up to an absurd value** (~106,512 observed) on a
  thin sample, risking a false PROMOTE. Fixed with a
  `MIN_SHARPE_SAMPLE_DAYS=20` floor.
- **`nifty_benchmark` was defined in code but never actually live** —
  `load_state()` only ever called `seed_registry()` on a brand-new
  ledger, so an *existing* ledger never picked up new seed entries
  added afterward. This is a structurally important fix: it means any
  future new registry key needs this same backfill path to actually
  reach a live ledger, which it now does, additively.
- **`health_check.py` (then, separately, `supervisor_check.py`)
  falsely flagged staleness/drift** when run against a local branch
  checkout, because `ledger.json` only ever auto-updates on `main`.
  Fixed twice, same root cause, same fix shape (`--live` flag fetching
  fresh from `main`). **This is the single most-repeated bug class in
  the project — always use `--live`.**
- **Crossover child names chained unboundedly** across generations.
  Truncated to `[:18]` chars + generation suffix.
- **Lineage was lost** on paper-tier demote-reset and never recorded
  at all for promotion-spawned children. Both fixed.
- **`advisors.py`'s `backtest()` silently swallowed exceptions** from
  `sig_*` functions. Added visible error-count logging.
- **A note saved via `dashboard.py`'s local Notes box silently didn't
  reach any Claude session** (hosted container's own throwaway disk,
  never committed). Fixed with an explicit warning + pointer to the
  real channel (Trading Floor Artifact note bowl).

---

## PART 6 — THE THING THAT KEEPS COMING UP: "WHY ISN'T IT TRADING MORE?"

Het has asked a version of this question multiple times, in different
framings ("agents show zero trades," "how do we make them trade
more," "make it more efficient"). The honest answer, checked against
real price data each time it came up, not assumed: **most contestants
show 0 trades because they're waiting for a genuinely rare real-world
event** (a >=3% single-day move happens roughly 13-25 days a year for
the leaders being watched). This was verified, not asserted — a
real-data diagnostic (`tools/diagnose_event_thresholds.py`) confirmed
`event_steel_t30/t40/t50` are effectively *unfireable* at current real
volatility (Tata Steel's max single-day move over 60 real trading days
was 2.72%, never crossing even the lowest 3% threshold), while
cement/infra fire rarely but genuinely (~1 qualifying day per 60).
This is presented to Het as a parameter question (his call whether to
loosen steel's threshold), never silently changed. The one real,
data-grounded action taken here (2026-08-28) was adding *additional*
threshold variants at each leader's real 85th percentile — never
touching the originals (Law 2).

**The deeper, recurring answer underneath all of these:** the
project's real bottleneck is calendar time, not compute, not agent
count, not session frequency. 126 days minimum before ANY verdict
counts. ~40 days in as of 2026-08-29. This cannot be accelerated
without either faking data or repeatedly re-testing the same fixed
historical window until something looks good — which is exactly what
Law 1 exists to prevent. The single highest-value action in Phase 1 is
almost always: let time pass, run the schedule, don't add machinery.

---

## PART 7 — CURRENT STATE SNAPSHOT (as of 2026-08-29 — this section WILL go stale, check `state.json` for the live number)

- Phase 1, standing mode. ~40 of 126 minimum days on rung for the
  oldest contestants.
- Zero promotions, ever. Rs 0 real money deployed anywhere. Both
  outcomes (edge exists / no edge) remain fully live possibilities.
- LADDER: `[0, 25_000, 50_000, 100_000, 200_000]` (raised from
  `[0, 10_000, 25_000, 50_000, 100_000]` 2026-08-25, Het's fresh
  sign-off, fixes a real rung-1 cost-friction problem).
- **27 defined in `seed_registry()`, 26 actually live in `ledger.json`
  — and that gap is normal, not a bug.** Spanning event_drift,
  momentum (including the new broad-market `mom_nifty100_lb90`),
  input_cost, monsoon (dormant), and the permanent Nifty benchmark;
  well under `MAX_CONTESTANTS=40`. **Learn this distinction — it
  causes real confusion:** merging a new key into `seed_registry()`
  does NOT put it in the ledger. `load_state()` backfills it only when
  `factory.py update()` next runs, so between a merge and the next
  scheduled run, `seed_registry()` and the ledger legitimately
  disagree by exactly the new keys. That gap is what `health_check.py`
  reports as its self-healing registry-drift warning, and it's also
  why a brand-new contestant does not appear on the dashboard (which
  reads the ledger, not the code) until the next run. On 2026-08-29
  this was verified end to end by actually rendering the dashboard
  headlessly — the new contestant was correctly absent, and the daily
  run's schedule (`factory.yml`: Mon-Fri 12:45 UTC, Sun 04:30 UTC) is
  what determines when it shows up.
- The old unattended dev-loop Routine is permanently retired.
  Standing operation: an hourly check-in Routine (platform's tightest
  allowed interval) + a free 15-min GitHub Actions supervisor.
- Dashboard (Streamlit, hosted by Het) and the Trading Floor Artifact
  are both live, both read-only, both reflect real committed data.

---

## PART 8 — THE ONE THING TO INTERNALIZE

If you read nothing else in this file: **this project's value is in
never lying to itself about the evidence.** Every real bug found here
was found by actually checking — running the diagnostic, dispatching
the workflow, reading the real job log, comparing branch vs main side
by side — not by assuming. Every declined request was declined by
naming the actual rule and the actual reasoning, not by vague caution.
Every merge waited for a fresh, explicit, in-session "yes," every
single time, no matter how the request was phrased or how much
apparent authority came with it. That discipline, kept up for another
~86 days of evidence-gathering (as of this writing), is the entire
point of the project succeeding at what it's actually trying to do —
which is finding out the truth, not making a number go up.
