# MASTER PLAN — the path from today to a real verdict

**Written 2026-08-29. Owner: Het. Executed by AI sessions.**

**This does NOT replace `EXECUTION_PLAN.md`.** That file holds the
settled facts, phase gates, kill conditions, and hard guardrails, and it
still wins on all of those. This file answers a different question:
*given where we actually are today — and given what the Q5 analysis just
found — what has to happen, in what order, for this project to produce a
trustworthy answer?*

Read `GOALS.md` for why. Read `EXECUTION_PLAN.md` for the rules. Read
this for the sequence.

---

## Where we actually are

- **Phase 1, day 40 of 126** minimum on-rung days. 26 contestants,
  all rung 0 (paper), **Rs 0 real money**, zero promotions ever.
- The machinery works and is genuinely well-tested: daily runs,
  weekly reports, cost model, tax model, benchmark contestant,
  monitoring, three dashboards, mechanical runbooks.
- **The measuring instrument has a serious flaw** (found 2026-08-29,
  `docs/research/Q5_statistical_power.md`): at 126 days with 26
  contestants, the promotion gate hands a PROMOTE to a *pure-noise*
  contestant ~85% of the time. It cannot currently separate skill from
  luck.

That last point reorders everything below. Building more strategy
machinery while the scoreboard can't tell truth from chance would be
the most expensive kind of wasted work — it would produce a confident
answer that means nothing.

---

## The one-sentence plan

**Fix the scoreboard before the scoreboard matters, let the calendar
run, and refuse to deploy real money until a promotion means something.**

---

## Critical path — in strict order

### STEP 1 — Fix the promotion bar — **DONE 2026-08-30 (on branch, unmerged)**

Het chose the recommended combination below and authorized it explicitly.
The bar now requires beating `nifty_benchmark` on date-paired excess
returns AND clearing a multiplicity-corrected Sharpe floor. Implemented,
tested, and committed *before* anyone looked at which contestants it
would promote — the ordering this section demanded. **Still needs a
separate merge decision to reach `main`**; until then the live runs use
the old bar. The original framing is kept below because the reasoning
still explains why this had to come first.

#### (original, for the record) Fix the promotion bar

**Why first:** every day of evidence collected under a broken bar is
evidence that can't be trusted later. This is cheap to fix now and
expensive to fix retroactively. Nothing else on this list matters if
this isn't done.

**The decision Het must make.** Five options are laid out in full in
`docs/research/Q5_statistical_power.md`. The recommendation, on the
analysis:

> **Require a promoted contestant to beat `nifty_benchmark`, not just
> an absolute bar — plus a multiplicity correction for the number of
> contestants.**

Why that combination: the benchmark contestant already exists (P0-3)
and shares the same market noise, so a *relative* test cancels most of
the common factor that's currently generating false positives. The
multiplicity correction handles the "26 lottery tickets" problem
directly. **Neither costs a single day of calendar time** — unlike
lengthening the window to ~3 years, which is the only other way to get
false positives to ~5%.

**This touches `RULES`. It is a hard-rule change. An AI session may
not make it.** Het decides; a session then implements, tests, and
waits for a separate merge confirmation.

**Acceptance criteria:** re-running `tools/analyze_statistical_power.py`
against the new gate shows a false-positive rate under ~10% at the
chosen N, and the change is committed *before* anyone looks at which
current contestants it would have promoted or failed.

### STEP 2 (automatic) — Let the calendar run

Day 40 of 126. **No amount of compute, agents, or session frequency
moves this.** One real trading day per calendar day. The daily and
weekly GitHub Actions runs already do this for free and unattended.

Sessions during this period should do RUNBOOK 1 and little else. The
correct amount of new machinery in Phase 1 is approximately zero.

### STEP 3 (at ~126 days, and only after STEP 1) — First honest verdict

The first contestant to clear the *corrected* bar is a **hypothesis**,
not a winner. Under the current design it would be a candidate for
rung-1 capital. Under an honest reading of Q5, one promotion is a
starting point for a test, not the end of one.

Expected outcomes, all legitimate:
- **Nothing clears the corrected bar** → this is a *real* result, and
  with a fixed bar the Section 5a kill condition can finally do its
  job. "Buy the index" is a successful outcome (`GOALS.md` says so
  explicitly).
- **Something clears it** → proceed to STEP 4. Do not fund it yet.
- **Something clears it but fails out-of-sample** → the promotion
  methodology itself is wrong (Section 5c), which is worth knowing.

### STEP 4 (gated on STEP 3) — Out-of-sample confirmation before capital

A contestant that clears the bar must then hold up on data it was
never evaluated against. This is the difference between an evidence
machine and a backtest.

Only after that does `GO_LIVE_CHECKLIST.md` get written and does the
question of real rupees even arise — and that is **Het's decision,
made deliberately, never automatic** (Law 3).

### STEP 5 (only if STEPS 3–4 succeed) — Phase 2

`EXECUTION_PLAN.md` Section 6 governs. Rung-1 capital, at most 1–3
strategies, every position ≥ Rs 25,000. Consistency with paper results
is the gate — *not* profit. Profit for reasons the paper model didn't
predict is luck, and luck is what this whole plan exists to filter out.

---

## Open research questions, ranked by value

From `EXECUTION_PLAN.md` Section 8. Q1, Q2 shipped in Phase 0. **Q5
answered 2026-08-29.** Remaining, in the order I'd do them:

| Q | Question | Why it matters | Cost |
|---|---|---|---|
| **Q4** | Does any contestant beat Nifty net of real cost+tax? | Directly the Phase 1→2 gate. **Now unblocked and next up** — it was deliberately held until after STEP 1 landed, because knowing the answer first would have contaminated the choice of promotion bar with hindsight. | Free, analysis only |
| ~~Q6~~ | **ANSWERED + FIXED 2026-08-30.** Do the 3 evolution mechanisms increase overfitting risk at this sample size? | Same failure family as Q5. Three breeding mechanisms sitting on 40 days of noise is exactly the overfitting risk Q5 quantified. Possibly the second-most-important open question. | Free, analysis only |
| **Q3** | Minimum viable position size per family | Feeds LADDER sizing. Partly answered by the P0-1 cost model. | Free |
| **Q8** | Full 10-year closed-loop model | Tests Fact 8 (contribution rate dominates return rate at this capital). Would tell Het where his effort is actually best spent — possibly *not* on trading at all. | Free |
| Q7 | Capacity ceiling per family | Almost certainly far above anything this project reaches. Confirm once, then stop worrying. | Free |
| Q9 | SEBI RIA/RA/PMS/AIF requirements | Only relevant Phase 4+. Partly researched already. | Free |
| Q10 | Highest-value change right now | **As of 2026-08-30: the bar is fixed (STEP 1 done, unmerged). The highest-value remaining action is merging it, then Q4, then waiting.** | — |

Q6 is the one I'd pick up next unprompted — it's the same class of
error as Q5, it's free, and the answer could mean disabling a breeding
mechanism during Phase 1 rather than letting it manufacture more
lottery tickets.

---

## What must NOT happen

These are the ways this project fails that have nothing to do with
markets:

1. **Deploying real money on an uncorrected bar.** The single most
   expensive possible mistake. STEP 1 exists to prevent it.
2. **Adding strategies, agents, or machinery during Phase 1.** More
   contestants = more lottery tickets = worse false-positive rate.
   Q5 quantified this: 26 → 40 contestants moves false positives from
   84% to 89%.
3. **Loosening `RULES` to make results look better.** Named explicitly
   as the Section 5f kill condition — the impulse itself is the signal.
   Note the asymmetry: STEP 1 *tightens* the bar. Tightening in
   response to an analysis that was blind to current results is the
   opposite of 5f, and is exactly what 5f is protecting.
4. **Treating a backtest, a synthetic test, or a paper result as
   realized profit.** Label everything. Always.
5. **F&O / leverage / AI-controlled capital allocation.** All declined,
   all logged, all needing their own dedicated conversations.

---

## Honest expected outcome

`GOALS.md` already says it and this plan doesn't soften it: **most
systematic retail trading attempts do not find a durable edge.** The
base rate is against a positive result, and the Q5 finding means the
project was, until today, likely to produce a *false* positive before
it produced a true one.

The value of this project is not that it will make money. It's that
it's being built so that if there's no edge, **we will actually find
that out** instead of believing a lucky number. Fixing the scoreboard
(STEP 1) is what makes that promise real rather than aspirational.

---

## Review triggers

Revisit this plan when any of these happen — not on a schedule:

- Het decides STEP 1 (rewrite STEPS 2–5 around the chosen option).
- A first contestant clears the bar.
- Q6 finds an evolution mechanism is manufacturing overfitting.
- Any kill condition in `EXECUTION_PLAN.md` Section 5 fires.
- Realized volatility moves materially from the 1.12% the Q5 numbers
  are calibrated to.
