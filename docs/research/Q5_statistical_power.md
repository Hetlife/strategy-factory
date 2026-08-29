# Q5 — When does this tournament's ranking become distinguishable from noise?

**Status:** ANSWERED, 2026-08-29. Reproduce with
`python3 tools/analyze_statistical_power.py` (seeded, deterministic).

**Question source:** `EXECUTION_PLAN.md` Section 8, Q5 — one of ten
research questions this project committed to answering "with
arithmetic." Q1 and Q2 shipped as Phase 0 work (P0-1, P0-2). Q5 had
never been answered.

**Evidence level: LEVEL 1 — THEORETICAL / SIMULATED.** This is a
null-hypothesis power analysis, not a claim about any real contestant's
performance. It says nothing about whether Het's strategies work. It
says what the *measuring instrument* can and cannot detect.

---

## The headline finding

**At the sample size RULES currently requires, the promotion gate
cannot distinguish skill from luck.**

Simulating a world where **no contestant has any edge whatsoever**
(true expected return exactly zero), using the project's own real
measured daily volatility (1.12%, pooled from the live ledger), and
running each simulated contestant through `factory.py`'s exact Sharpe
estimator and exact promotion gate:

| days in market | P(≥1 zero-edge contestant PROMOTED), K=26, corr 0.5 |
|---|---|
| 63 | 90.9% |
| **126 (current `min_days_on_rung`)** | **84.8%** |
| 252 | 65.5% |
| 504 | 23.5% |
| 756 | 4.9% |
| 1260 | 0.1% |

With 26 contestants assumed independent (an upper bound, since real
contestants share Indian equity beta), the false-positive rate at 126
days is **~100%**.

**Plain version:** if the entire premise of this project is wrong and
not one strategy has any real edge, the tournament would still hand out
a PROMOTE roughly 85 times out of 100 at the 126-day mark. A promotion
under current rules is therefore close to uninformative on its own.

## Why — the arithmetic, checkable by hand

Two independent derivations agree, which is why I trust this:

**1. Analytic.** Under the null, the annualized Sharpe estimator is
approximately `N(0, 252/n)`. At n=126 its standard deviation is
`√(252/126) = 1.41`. The bar `min_sharpe = 0.4` therefore sits only
**0.28 standard deviations above zero** — so a *single* zero-edge
contestant clears the Sharpe bar ~39% of the time. That is not a
demanding test; it is close to a coin flip.

**2. The binding constraint is actually expectancy, not Sharpe.**
`min_expectancy = 0.0005/day`. Under the null the sample mean has
standard deviation `0.01119/√126 = 0.000997`, so the bar is 0.50 SD
above zero → ~31% pass. Meanwhile `sharpe ≥ 0.4` is equivalent to
`mean ≥ 0.4 × 0.01119 / √252 = 0.00028`, which is *looser* than the
0.0005 expectancy bar. So the two "independent-looking" gates are
largely the same test applied twice, and the tighter one dominates.
They do not stack the way two separate filters would.

**3. Multiple comparisons.** ~26 contestants each getting a ~26% shot
(after the drawdown filter) means the probability that *none* of them
gets lucky is small. Correlation between contestants helps — it reduces
the effective number of independent bets — but only from ~100% down to
~85%, not to anything acceptable.

## The second-order finding, which may matter more

`EXECUTION_PLAN.md` Section 5a defines a kill condition:

> "After 12 months of live paper trading, no strategy clears the RULES
> bar → stop."

**That kill condition is unreliable in the dangerous direction.**
Because the bar is cleared ~85% of the time by pure chance at 126 days,
the "no strategy cleared it" outcome is unlikely to occur *even if
there is genuinely no edge*. The kill condition is supposed to be the
project's honest off-ramp. As configured, it will rarely fire, so it
cannot do the job it was written to do.

This is exactly the failure mode `EXECUTION_PLAN.md` Section 5f warns
about — a system that ends up flattering itself — arriving through
statistics rather than through anyone bending a rule.

## How many contestants the arena can afford

At the current 126-day requirement, correlation 0.5:

| contestants | false-positive rate |
|---|---|
| 1 | 25.6% |
| 5 | 59.7% |
| 10 | 72.5% |
| 26 (today) | 84.4% |
| 40 (`MAX_CONTESTANTS`) | 88.9% |

Every contestant added makes a false promotion more likely. The
tournament format — the project's core design — is itself a
multiple-comparisons machine. That is not a reason to abandon it, but
it is a reason the promotion bar must be far stricter than a bar for a
single pre-chosen strategy would need to be.

## What this does NOT say

- It does **not** say any current contestant is fake, lucky, or
  failing. No live contestant's returns were examined for this. The
  analysis is deliberately blind to them, which is what
  `state.json`'s `P3-rules-threshold-review` demanded: *"argument must
  be written BEFORE looking at effect on current contestants (avoid
  hindsight bias)."* That condition is satisfied here.
- It does **not** say the strategies have no edge. It says the
  instrument currently can't tell either way at 126 days.
- It does **not** prescribe new thresholds. `RULES` is a protected
  financial parameter (CLAUDE.md hard rule) and was **not changed**.

## Options, for Het's decision — not acted on

These are the honest levers. Each has a real cost; none is free.

1. **Lengthen the evidence window.** Getting false positives to ~5%
   needs ~756 days in market (~3 years) at 26 contestants. Very
   strong, very slow — well beyond the current 12-month plan.
2. **Shrink the arena.** Fewer contestants means fewer lottery
   tickets. 26 → 5 cuts the false-positive rate from 84% to 60% at
   the same N. Still not good, but directionally right, and free.
3. **Raise the bar for the multiplicity.** A Bonferroni-style
   correction (require the promoted contestant to clear a threshold
   set for 26 simultaneous tests, not one) is the statistically
   standard answer and costs no calendar time.
4. **Require the contestant to beat `nifty_benchmark`, not just an
   absolute bar.** The benchmark already exists (P0-3) and shares the
   same market noise, so a relative test cancels much of the common
   factor — this is likely the highest-value, lowest-cost change.
5. **Accept it explicitly**, treating a first promotion as a
   hypothesis to be tested with fresh out-of-sample data rather than
   as a verdict — i.e. never let rung-1 capital follow directly from
   one promotion.

Option 4 combined with 3 is, on this analysis, the strongest
risk-adjusted answer. **All of them touch `RULES` or `LADDER`
behaviour and therefore require Het's explicit, separate
authorization.** Logged in `het_directives.md` under NEEDS HET.

## Reproducing / auditing this

```bash
python3 tools/analyze_statistical_power.py
```

Seeded (`seed=7`, 20,000 trials/cell), reads `RULES` live from
`factory.py` so it cannot drift from the real thresholds, writes
nothing. The `K=1 independent` and `K=1 correlated` cells should agree
within Monte Carlo error — they do (26.5% vs 25.6%), which is a
built-in validity check on the correlation machinery.

If the arena's realized volatility moves materially away from 1.12%,
re-measure it from the ledger and re-run; the conclusion is not
sensitive to small changes but the exact percentages are.
