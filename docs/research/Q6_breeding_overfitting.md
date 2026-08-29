# Q6 — Does the evolution system increase overfitting risk?

**Status:** ANSWERED, 2026-08-29. **Yes, materially.** Reproduce with
`python3 tools/analyze_breeding_overfitting.py` (seeded, deterministic).

**Question source:** `EXECUTION_PLAN.md` Section 8, Q6. Companion to
Q5 (`Q5_statistical_power.md`) — same null-hypothesis method.

**Evidence level: LEVEL 1 — THEORETICAL / SIMULATED**, plus one
**LEVEL 3 (direct code inspection + live-ledger verification)** finding
below that is a matter of fact, not simulation.

---

## Finding 1 (fact, not simulation): a documented safety gate does not exist

**The docs say breeding cannot fire until 126 days. That is false for
one of the two mechanisms.**

- `propose_evolutions()` (advisor-evolve) **does** gate on
  `days_on_rung >= RULES["min_days_on_rung"]` and `trades >= min_trades`.
  Verified by reading the code.
- `attempt_breeding()` (crossover) **does not**. Its only eligibility
  conditions are: rung 0, not retired/evolved-out/permanent, ranked in
  the top `BREEDING_TOP_N`, **`equity > 1.0`**, and
  **`trades >= BREEDING_MIN_TRADES` (10)**. There is no days gate at all.

So crossover can fire the moment any paper contestant is simultaneously
profitable and has 10 trades — which could be at day 40, or day 25.

**Two places in the repo claimed otherwise** and needed correcting:
`RUNBOOKS.md`'s "things that look broken but aren't" table and
`next_session.md`. Both said *both* mechanisms need 126 days. (I first
wrote "three places," expecting `PROJECT_STUDY.md` to carry it too --
it does not. Corrected rather than left as a rounder-sounding number.)

**Why it hasn't fired yet — verified against the live ledger, not
assumed:** no contestant currently satisfies both conditions at once.
`mom_cement_lb60` has 13 trades but equity 0.944 (unprofitable).
`input_cost_lag` has equity 1.012 but only 2 trades. **The protection
everyone believed was structural is actually coincidental.**
`mom_cement_lb60` or `mom_cement_lb40` (12 trades) needs only a
profitable stretch to trigger breeding — plausibly within weeks.

## Finding 2 (simulated): the breeding gate is close to a coin flip

Crossover selects parents on `equity > 1.0`. Under an explicit
zero-edge null, calibrated to the project's real measured 1.12% daily
volatility and including the weekly paper holding-cost decay:

| days | P(a PURE-NOISE contestant looks profitable) |
|---|---|
| 20 | 45.1% |
| **40 (roughly today)** | **43.2%** |
| 63 | 41.1% |
| 126 | 37.9% |
| 252 | 32.6% |
| 504 | 25.9% |
| 756 | 20.9% |

At the sample sizes where crossover can currently fire, "profitable"
carries **almost no information about skill**. A contestant with no
edge whatsoever clears that bar roughly two times in five. Breeding
from those parents is selecting luck and then propagating it into
children — which is overfitting with extra steps.

(The rate sits below 50% even at 20 days because compounding of
zero-mean returns plus the holding tax both drag median equity below
1.0. The gap from 50% is drag, not signal.)

## Finding 3: breeding makes Q5's problem worse in two ways

1. **More lottery tickets.** Breeding adds up to
   `BREEDING_MAX_NEW_PER_ROUND = 3` contestants per weekly round,
   growing the arena toward `MAX_CONTESTANTS = 40`. From Q5, at 126
   days with correlation 0.5: 26 contestants → **84.4%** chance a
   pure-noise contestant is promoted; 40 contestants → **88.9%**.
2. **Q5's numbers are a floor, not a ceiling.** Q5 modelled a *fixed*
   set of 26 contestants. Breeding churns the population — children
   born, stragglers retired or evolved out — so the number of
   *distinct hypotheses the tournament tests over its life* is larger
   than the number alive at any instant. Standard multiple-comparisons
   logic applies to the cumulative count, not the concurrent one.

## Answer to Q6, and the recommendation

**Should any mechanism be disabled during Phase 1?**

Not disabled — **gated**, to match its sibling. The narrow, consistent
fix:

> Add `days_on_rung >= RULES["min_days_on_rung"]` to
> `attempt_breeding()`'s eligibility check, exactly as
> `propose_evolutions()` already has it.

Why this specific fix:
- It makes the code do **what all the documentation already claims it
  does** — so it is arguably a bug fix, not a policy change.
- It is one condition in one function, mirroring a line that already
  exists five hundred lines earlier in the same file.
- It touches **no** `RULES` / `LADDER` / `COST_PER_SIDE` value.
- It does not disable a mechanism Het explicitly asked for; it delays
  it until there is enough evidence for "profitable" to mean something.

**It does change live evolution dynamics**, which by the precedent set
for the paper-holding-cost-decay change means it needs Het's fresh
confirmation before merging. Not done unilaterally.

The alternative — leaving it as-is — means accepting that the first
breeding event will likely occur on ~40–60 days of data, at which point
"profitable" is a 43% coin flip, and the resulting children inherit
noise-selected parameters while consuming contestant slots.

## What this does NOT say

- It does **not** say breeding is a bad idea. It says breeding **too
  early** selects noise. The mechanism itself is sound once there is
  enough evidence behind the fitness signal.
- It does **not** examine whether any current contestant's performance
  is real. Deliberately blind to that, same as Q5.
- It does **not** change anything. No code was modified.

## Reproducing

```bash
python3 tools/analyze_breeding_overfitting.py   # this analysis
python3 tools/analyze_statistical_power.py      # Q5, the companion
```

Both are seeded, read live constants from `factory.py` so they cannot
drift from the real thresholds, and write nothing.
