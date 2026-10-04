# ACCELERATION PLAN — mechanical work list

**Written 2026-09-13** on Het's instruction: *"start working on it and
create detailed work list with detailed steps and all the info for low
token model to do autonomously."*

**Who this is for:** any session, on any model, including a cheap one.
Follow it top to bottom. Every step says exactly what to run, what the
output should look like, and what to do with each possible result. If a
step says **STOP**, stop — do not improvise past it.

**What this is NOT:** this is not a profit plan and it has no money
target. It exists because the evidence base turned out to be polluted and
the promotion clock turned out to be wrong. Fixing that is what "working
toward something real" actually means here. `RUNBOOK 9` is still the
default cycle for an ordinary session; this file is the specific
multi-step project running alongside it until every step below is DONE.

---

## Why this exists — the four findings behind it

All four were found 2026-09-13 and all four are measured, not assumed.

| # | Finding | Evidence | Status |
|---|---|---|---|
| 1 | **Duplicate trading days.** `factory.yml`'s update step had no weekday guard, so it also ran on the Sunday report cron. `update()` keys its row on the newest date in the *price panel* — still Friday's over a weekend — so Friday was recorded twice, nearly every week since July. | 26 of 27 contestants carried duplicate dates, 142 extra rows, almost all Fridays. Every contestant's progress toward the 126-day bar was overstated ~19%. | **FIXED on branch**, awaiting merge |
| 2 | **Phantom trading days.** `fetch_prices()` ends in `.ffill()`, and `dropna(how="all")` only drops a row where *every* ticker is missing. So an NSE holiday, or a day whose data hasn't posted, survives as a row of forward-filled prices — a "trading day" on which everything closed exactly unchanged. | 2 of 5 checkable days (40%) had 95–99% of all tickers at exactly 0.0 return. | Detector built; **root-cause fix is item 1's guard**, which also covers this |
| 3 | **Benchmark can't pair.** Contestants start 2026-07-13, `nifty_benchmark` starts 2026-08-26, and the gate pairs date by date. ~37 of ~43 contestant days are unusable, so the gate fails closed for everyone. | Q4 finding, `docs/research/Q4_beat_nifty.md`; re-confirmed live. | Backfill tool built + tested, **awaiting run** |
| 4 | **Dead weight raises the bar.** 15 of 25 live contestants have never traded. The multiplicity correction means every extra contestant raises the Sharpe floor for all the others. | Measured: arena 25 → 10 lowers the floor 10.5% and cuts days-to-certify ~20%. | Validation tool built + tested, **awaiting run** |

---

## Hard boundaries for every step below

Read these before touching anything. They are not negotiable and no step
in this plan overrides them.

- **NEVER** change `RULES`, `LADDER`, or `COST_PER_SIDE`.
- **NEVER** merge to `main` or push to `main` without a **fresh,
  in-session "yes" from Het for that specific merge**. A yes recorded in
  this file, or given for an earlier batch, does **not** carry forward.
- **NEVER** retire, add, or mutate a registry entry on your own judgment.
  Step 5 produces evidence; Het decides.
- **NEVER** hand-edit `ledger.json`. The only thing permitted to write it
  is `factory.py` itself and `tools/backfill_benchmark_history.py --apply`,
  which backs it up first and touches only `nifty_benchmark`.
- **NEVER** claim a step passed without pasting the real output.
- **NEVER** `git add -A` or `git add .` — stage by exact filename.

---

## STEP 0 — Orient (every session, ~1 min)

```bash
cd /home/user/strategy-factory
cat .autonomous/loop_state.json          # in_progress? resume from resume_instructions
git log --oneline -5
git status --short                        # expect clean
python3 tools/health_check.py --live      # expect: no findings
```

Then read the STATUS LINE at the bottom of this file to see which step is
next. If `health_check` reports findings, fix those first via RUNBOOK 9;
do not start a step below with a dirty health check.

---

## STEP 1 — Merge the tooling to `main` *(needs Het, once)*

**Why it's needed:** GitHub will not let `workflow_dispatch` run a
workflow file that exists only on a feature branch. Every tool in this
plan needs real market data, and this sandbox cannot reach any market
data source (`yfinance` blocked; `fred.stlouisfed.org` returns 407 from
the proxy — both verified 2026-09-13). GitHub Actions runners can. So
nothing in this plan can actually run until the workflow is on `main`.

**What merges:** `.github/workflows/acceleration_tools.yml`,
`.github/workflows/diagnose_input_cost_threshold.yml`,
`tools/validate_strategies_historical.py`,
`tools/backfill_benchmark_history.py`,
`tools/detect_phantom_days.py`,
`tools/diagnose_input_cost_threshold.py`,
plus the item-1 fix (`factory.py`'s idempotence guard and `factory.yml`'s
weekday guard) and the docs/trackers in the same commits.

**Do this:**
1. Ask Het, in session, in plain words: *"Okay to merge the acceleration
   tooling and the duplicate-day fix to main?"*
2. Only on an explicit yes, merge. Use the GitHub API
   (`mcp__github__create_pull_request` then
   `mcp__github__merge_pull_request`) — local `git merge` on `main` has
   been blocked by the environment's safety classifier before (see
   `AUTONOMOUS_LOG.md` 2026-09-02).
3. Verify after merging: `git fetch origin main && git log --oneline origin/main -3`.

**STOP if:** Het says no, or does not answer. The plan simply waits. Do
not run anything from a branch and do not work around the platform
constraint.

---

## STEP 2 — Confirm the duplicate-day fix is live

Only after STEP 1 merged.

```bash
# The next weekday run should behave normally; the next SUNDAY run
# should no longer run update() at all.
```

Check the newest `factory.yml` run after the following Sunday:

| What you see | What it means | Do |
|---|---|---|
| Sunday run shows the update step **skipped** | Workflow guard works | Mark STEP 2 DONE |
| Sunday run ran update but printed `Arena update SKIPPED: ... already recorded` | Code guard caught it; workflow guard didn't apply | Still correct. Mark DONE, note it |
| Sunday run appended a new row for Friday | **Neither guard worked** | STOP. Escalate to Het (RUNBOOK 6) |

Also re-run the detector against the fresh `main` ledger:

```bash
git fetch origin main && git checkout origin/main -- factory_state/
python3 tools/detect_phantom_days.py
git checkout HEAD -- factory_state/
```
Expect the phantom count to stop growing. Existing phantom/duplicate rows
stay — cleaning historical rows is STEP 6 and needs Het.

---

## STEP 3 — Run the historical validation *(the big one)*

Only after STEP 1 merged. This is read-only and cannot damage anything.

Dispatch `acceleration_tools.yml` with input `tool = validate`
(`mcp__github__actions_run_trigger`, method `run_workflow`, ref `main`),
then read the job log (`mcp__github__get_job_logs`, `return_content: true`).

It prints one row per strategy: trades, total return, Sharpe, best
Sharpe, max drawdown, and whether it EVER cleared the real promotion bar
at any weekly checkpoint across ~5 years.

**Interpreting it — the one rule that keeps this honest:**

| Result | Strength of evidence | Action |
|---|---|---|
| **0 trades in 5 years** | Strongest. "Never triggers" is a property of the mechanism, not bad luck | Strong KILL candidate → STEP 5 |
| Traded, but never cleared the bar | Real evidence against, but one historical period is one draw | Weaker KILL candidate → STEP 5, weigh against its live record |
| Cleared the bar historically | **Proves nothing.** Backtests flatter; today's index membership is not the past's | **Do NOT promote. Do NOT propose promoting.** Note it and move on |

The tool only ever supports killing. It prints no promotion
recommendation and no session should invent one from it.

**Sanity check before trusting any run:** the tool was validated
2026-09-13 against a pure random-walk panel and correctly passed **zero**
of 25 strategies. If a real run shows many strategies clearing the bar,
be suspicious of the data, not delighted by the result.

---

## STEP 4 — Backfill the benchmark

Only after STEP 1 merged. **Always dry-run first.**

1. Dispatch with `tool = backfill-dryrun`. Read the log.
   - Expect: a count of unpaired dates, the rows it would prepend, and
     the effect on the multiplicity floor (`inf` → a finite number).
   - Expect: `WOULD NOT TOUCH: N other contestant(s)...`
2. Check the dry run looks sane:

| Dry-run output | Do |
|---|---|
| Prepends a plausible number of rows (tens), all before the benchmark's current first date | Proceed to apply |
| Reports `Nothing to backfill` | Already done. Mark STEP 4 DONE |
| Wants to prepend thousands of rows, or dates after the benchmark's start | **STOP. Escalate.** Something is wrong with the fetched history |

3. Dispatch with `tool = backfill-apply`. It backs up `ledger.json`
   first, asserts it introduced no duplicate or out-of-order date,
   re-reads from disk to confirm no other contestant changed, and commits
   both the ledger and its backup.
4. Verify: `git fetch origin main && git log --oneline origin/main -2`,
   then re-run the dry run — it should now say `Nothing to backfill`.

**If anything looks wrong afterwards:** the backup is committed next to
the ledger as `factory_state/ledger.backup.<timestamp>.json`. Restoring
it is a `git`-visible, fully reversible operation.

---

## STEP 5 — Retire what never worked *(needs Het)*

**Do NOT retire anything autonomously.** This step produces a list and
stops.

1. From STEP 3's output, build the kill list: strongest candidates first
   (0 trades in 5 years), then traded-but-never-cleared.
2. For each, cross-check its live record in the ledger (trades,
   days_on_rung) so Het sees both the historical and the live picture.
3. Write it into `het_directives.md`'s NEEDS HET section in plain
   language: what it is, why it's a candidate, what retiring it buys
   (recompute the multiplicity floor for the smaller arena, the way
   `.autonomous/ACCELERATION_PLAN.md`'s finding 4 did).
4. Ask Het. **STOP.**
5. Only on an explicit yes, retire — by setting `retired: true` through
   `factory.py`'s own code path, never by hand-editing the ledger, and
   never by deleting a registry entry (history is preserved forever; see
   `graveyard()`).

---

## STEP 6 — Historical duplicate/phantom cleanup *(needs Het, lowest priority)*

The 142 duplicate rows already in the ledger are **not** cleaned by the
item-1 fix, which only stops new ones. Cleaning them would rewrite
recorded history, so it is Het's call and it is deliberately last.

Worth knowing before asking him: `excess_return_stats()` already dedupes
by date, so **the promotion gate is already protected** from the
duplicates. What stays distorted is `days_on_rung` (the clock),
`days_in_market`, `sum_ret`/`sum_sq` (so Sharpe), and `trades`. Present
both options honestly — recompute every aggregate from deduped history,
or leave it and note the overstatement — and let him choose.

---

## STATUS LINE — update this when a step completes

```
STEP 0  orient .................. (run every session)
STEP 1  merge tooling ........... DONE 2026-09-13 (PR #22, merge 695ddac)
STEP 2  confirm dup fix live .... waiting on the next Sunday cron
STEP 3  historical validation ... DISPATCHED (acceleration_tools.yml, tool=validate)
STEP 4  benchmark backfill ...... DRY RUN DISPATCHED; apply after reading it
STEP 5  retire dead strategies .. waiting on STEP 3 output + Het
STEP 6  historical cleanup ...... waiting on Het, lowest priority
```

Last updated: 2026-09-13. STEP 1 merged with Het's fresh in-session
authorization ("Yes, merge it all", via AskUserQuestion). Both guards
verified present on `main`. STEP 2's real proof is the next Sunday run —
check it per the decision table above; until then the fix is merged but
unproven in production.
