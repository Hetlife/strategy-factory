# Q4 — Does any contestant beat Nifty, net of real cost and tax?

**Status: ANSWERED 2026-09-03. The answer is NO — and the more useful
finding is *why the question cannot yet be meaningfully asked*.**

Reproduce with `python3 tools/analyze_q4_vs_benchmark.py` (read-only,
fetches the live ledger, writes nothing).

**Evidence level: 6** — paper/shadow execution on real market prices,
net of a realistic cost model. Not realized profit. Rs 0 at risk.

**Question source:** `EXECUTION_PLAN.md` Section 8, Q4 — the Phase 1 →
Phase 2 gate question. Deliberately held until after the Q5 promotion-bar
fix was committed, so that knowing the answer could not influence the
choice of bar (`MASTER_PLAN.md`'s no-hindsight requirement).

---

## The headline

**Zero of 25 live contestants beat the benchmark with 95% confidence.**

Not one. And no contestant is ahead on the post-tax comparison either —
most are losing outright.

But the point estimates are not the interesting part. Three structural
findings below matter far more than any current number.

---

## Finding 1 — The measurement window is ~6 days, not 44

The benchmark contestant (`nifty_benchmark`) only began accumulating
history on **2026-08-26**. The older contestants started **2026-07-13**.

| | first history date | days of history |
|---|---|---|
| `nifty_benchmark` | 2026-08-26 | 7 |
| typical contestant | 2026-07-13 | 44 |

Because the comparison is **date-paired** (deliberately — that is what
cancels the shared market move), the usable sample is capped by the
*shorter* of the two. Every contestant therefore has only **4–7 paired
days** against the benchmark, regardless of having 44 days of its own.

At that sample size the 95% confidence intervals are enormous — often
±0.9% *per day* — and every single one straddles zero. Nothing here is
distinguishable from noise, in either direction.

## Finding 2 — The apparent "winners" are an artifact of not trading

**15 of the 26 live contestants have made ZERO trades in 44 days.**
The entire `event_*` family, `input_cost_*`, and `monsoon_cement` have
never fired: their thresholds have not been crossed by real volatility.

Those 15 sat in cash. The index fell over this window. A position of
"nothing" therefore shows a *positive* excess return versus a falling
benchmark — and they cluster at exactly the same `+0.00014/day`, which
is simply the benchmark's own loss with the sign flipped.

**That is not alpha. It is non-participation.** Any reading of the
results table that treats those rows as outperformance is wrong, and
the identical values across unrelated strategies are the tell.

This also means the *effective* arena is ~11 contestants generating
evidence, not 26. The other 15 are consuming slots and contributing
nothing — which is separately worth Het's attention, because the
`event_*` threshold question was already flagged for steel on
2026-08-27 and this shows it is true across cement and infra too.
That is registry-parameter territory: **not changed here.**

## Finding 3 — The merged Q5 gate has restarted the promotion clock

This is the operationally important one, and it is a direct, verified
consequence of the Q5 fix merged 2026-09-02 (PR #21).

The new gate requires a date-paired excess Sharpe against the benchmark.
`excess_return_stats()` returns NaN below `MIN_SHARPE_SAMPLE_DAYS` (20
paired days), and `multiplicity_sharpe_floor()` then returns `inf`. So
the gate currently reports, verbatim, for every contestant:

```
excess sharpe vs benchmark, corrected for 25 simultaneous contestants:
  have NaN (under min sample), need >= inf
  (cannot certify -- too few paired days against the benchmark)
```

**No contestant can be promoted right now on any performance, because
there is not yet enough benchmark history to certify against.** The gate
is failing closed — exactly as designed, and the safe direction — but
the consequence is real:

> The effective promotion clock now runs from the **benchmark's** start
> date (2026-08-26), not the contestants' (2026-07-13). The 126-day
> minimum will be satisfied by the contestants roughly six weeks before
> it is satisfiable against the benchmark.

This is not a bug and needs no emergency fix. It does mean the earliest
possible honest promotion moved later by about six weeks. Het should
know that, because it changes the date at which this project produces
its first real verdict — and "when will we know" is one of the questions
`GOALS.md` exists to answer honestly.

**Options, for Het — none taken here:**
1. **Do nothing.** Let the benchmark accumulate history like everything
   else. Costs ~6 weeks of calendar, changes no code, risks nothing.
   This is the default and probably correct.
2. **Backfill the benchmark's history** so pairing can use the full 44
   days. This would require writing historical rows into `ledger.json`,
   which is a hard-rule action (never hand-edit the ledger) and would
   also mean the benchmark's own returns were computed retroactively
   rather than observed live — weaker evidence, and a precedent worth
   avoiding.

Recommendation: option 1. The six weeks cost nothing real, and option 2
trades away exactly the "observed live, not reconstructed" property that
makes this evidence worth collecting at all.

## Finding 4 — This window is a falling market, so the bar is currently low

The benchmark's own mean daily return over its 6 days is **−0.000563**
(≈ −14.2% annualised). Over such a short window that figure is itself
meaningless as a market forecast, but it does mean that "beating the
benchmark" right now mostly measures *who lost less* or *who wasn't
invested*. It is not the regime in which outperformance is informative.

## The tax asymmetry, which does not go away

Worth stating plainly because it is a permanent structural headwind, not
an artifact of this window:

- A buy-and-hold index position eventually pays **LTCG, 12.5%**.
- A strategy turning over inside 12 months pays **STCG, 20%**.

An active strategy must out-earn the index by enough to cover that
**7.5-percentage-point tax gap** *before* it is worth running at all —
on top of the round-trip trading costs already charged in every stored
return. This is a real part of the Phase 1 → 2 decision and is the
reason the post-tax column, not the gross one, is the one that counts.

---

## What this does NOT say

- It does **not** say the strategies have failed. 6 paired days cannot
  fail anything. It says the measurement is not yet possible.
- It does **not** say the index will keep falling, or that a falling
  window tells us anything about the future.
- It does **not** say the 15 non-trading contestants are broken. Their
  thresholds may be correctly conservative; they simply have not fired.
- It changes **nothing**. No code, no `RULES`, no registry entry, no
  ledger. Findings 2 and 3 both name decisions that are Het's.

## Reproducing

```bash
python3 tools/analyze_q4_vs_benchmark.py    # this analysis
python3 tools/analyze_statistical_power.py  # Q5, the promotion bar
python3 tools/analyze_breeding_overfitting.py  # Q6, the breeding gate
```

All three are read-only, reuse `factory.py`'s own live functions so they
cannot drift from real behaviour, and write nothing.
