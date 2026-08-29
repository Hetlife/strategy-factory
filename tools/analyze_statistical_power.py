"""
Answers EXECUTION_PLAN.md Section 8's Q5 -- the research question the
project committed to answering with arithmetic and never did:

  "At what N (sample size / calendar date) does the tournament's ranking
   become statistically distinguishable from noise?"

WHY THIS MATTERS MORE THAN ANY FEATURE: this project runs a tournament
of ~26 contestants and promotes whichever clears RULES. With that many
competitors, the best-looking one will look good BY CHANCE even if no
contestant has any real edge at all. If the promotion bar sits below
what pure luck produces at the sample size RULES requires, then a
"PROMOTE" verdict measures luck, not skill -- and every downstream
decision (real capital via LADDER) inherits that error. That is the
multiple-comparisons problem, and it is the single most likely way an
honest-looking evidence machine still fools itself.

METHOD: Monte Carlo under an explicit NULL hypothesis -- every
contestant has ZERO true edge. Returns are drawn to match the project's
own REAL observed daily volatility (1.12%, measured from the live
ledger's pooled non-zero daily returns, 2026-08-29), not an assumed
number. Each simulated contestant is run through factory.py's EXACT
accounting (same equity compounding, same peak/drawdown tracking, same
sum_ret/sum_sq Sharpe estimator, same annualization) and then through
the EXACT promotion gate from RULES. We then measure how often pure
noise produces a PROMOTE.

Correlation matters: real contestants trade overlapping Indian equities
and are NOT independent, which reduces the effective number of
independent bets. Both the independent case (upper bound on false
positives) and a realistically correlated case are reported.

This script CHANGES NOTHING. It reads RULES from factory.py so it can
never drift from the live thresholds, and writes no state. It is
analysis, explicitly sanctioned by EXECUTION_PLAN.md Section 8, not new
machinery (Phase 1 forbids adding strategy families / evolution
mechanisms, not answering the project's own research questions).

Deterministic: seeded, so any session re-running this gets identical
numbers and can verify the claim rather than trust it.

USAGE: python3 tools/analyze_statistical_power.py
"""
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import factory

# Measured 2026-08-29 from the live ledger on main: pooled std of all
# non-zero daily contestant returns (n=235). Recompute if the arena's
# character changes materially; don't assume this stays right forever.
REAL_DAILY_VOL = 0.01119

N_TRIALS = 20000
SEED = 7


def simulate_contestants(n_contestants, n_days, vol, corr, rng):
    """Returns (mean, sharpe, max_drawdown) arrays, computed exactly the
    way factory.py's report() does, for n_contestants under a TRUE ZERO
    edge over n_days days_in_market.

    corr: pairwise correlation between contestants, via a single shared
    market factor -- crude but the right shape (real contestants share
    Indian equity beta). corr=0 gives independent contestants.
    """
    # one shared factor + idiosyncratic, scaled so total vol == vol
    shared = rng.standard_normal((n_days, 1))
    idio = rng.standard_normal((n_days, n_contestants))
    r = (np.sqrt(corr) * shared + np.sqrt(1.0 - corr) * idio) * vol

    # factory.py: mean = sum_ret/n ; var = sum_sq/n - mean^2
    sum_ret = r.sum(axis=0)
    sum_sq = (r ** 2).sum(axis=0)
    mean = sum_ret / n_days
    var = np.maximum(sum_sq / n_days - mean ** 2, 1e-12)
    sharpe = mean / np.sqrt(var) * np.sqrt(252)

    # factory.py tracks equity multiplicatively and drawdown vs running peak
    equity = np.cumprod(1.0 + r, axis=0)
    peak = np.maximum.accumulate(equity, axis=0)
    max_dd = (equity / peak - 1.0).min(axis=0)

    return mean, sharpe, max_dd


def false_positive_rate(n_contestants, n_days, corr, rules, rng, trials=N_TRIALS):
    """P(at least one zero-edge contestant clears the promotion gate).

    Applies the gate factory.py actually applies at promotion time:
    mean >= min_expectancy AND sharpe >= min_sharpe AND drawdown better
    than max_drawdown. (days_on_rung and trades are separate calendar/
    activity gates, not statistical ones -- noted in the writeup.)
    """
    any_pass = 0
    sharpe_max = []
    for _ in range(trials):
        mean, sharpe, max_dd = simulate_contestants(
            n_contestants, n_days, REAL_DAILY_VOL, corr, rng)
        passes = ((mean >= rules["min_expectancy"])
                  & (sharpe >= rules["min_sharpe"])
                  & (max_dd >= rules["max_drawdown"]))
        if passes.any():
            any_pass += 1
        sharpe_max.append(sharpe.max())
    return any_pass / trials, float(np.mean(sharpe_max))


def main():
    R = factory.RULES
    print("Q5 — STATISTICAL POWER OF THE TOURNAMENT (null: NO contestant has any edge)")
    print("=" * 78)
    print(f"Live RULES (read from factory.py, not hardcoded here):")
    print(f"  min_days_on_rung = {R['min_days_on_rung']}   min_trades = {R['min_trades']}")
    print(f"  min_expectancy   = {R['min_expectancy']}   min_sharpe = {R['min_sharpe']}")
    print(f"  max_drawdown     = {R['max_drawdown']}")
    print(f"Real measured daily vol used for the null: {REAL_DAILY_VOL:.5f}")
    print(f"Monte Carlo trials per cell: {N_TRIALS}, seed={SEED}\n")

    # --- analytic sanity check, so the simulation can be verified ---
    n = R["min_days_on_rung"]
    analytic_sharpe_sd = np.sqrt(252.0 / n)
    thresh_in_sd = R["min_sharpe"] / analytic_sharpe_sd
    print("ANALYTIC CHECK (independent of the simulation):")
    print(f"  Under the null, ANNUALIZED Sharpe ~ N(0, 252/n).")
    print(f"  At n={n} days in market, its standard deviation is {analytic_sharpe_sd:.2f}.")
    print(f"  So min_sharpe={R['min_sharpe']} sits just {thresh_in_sd:.2f} SD above zero")
    print(f"  -> a SINGLE zero-edge contestant clears the Sharpe bar "
          f"~{100*(1-_norm_cdf(thresh_in_sd)):.0f}% of the time.\n")

    rng = np.random.default_rng(SEED)

    print("FALSE-POSITIVE RATE — P(at least one zero-edge contestant is PROMOTED)")
    print("-" * 78)
    print(f"{'days_in_market':>14} | {'K=26 indep':>11} | {'K=26 corr .5':>13} | "
          f"{'K=1 indep':>10} | {'E[best Sharpe]':>14}")
    print("-" * 78)
    for n_days in (63, 126, 189, 252, 504, 756, 1260):
        fp_indep, best_sh = false_positive_rate(26, n_days, 0.0, R, rng)
        fp_corr, _ = false_positive_rate(26, n_days, 0.5, R, rng)
        fp_one, _ = false_positive_rate(1, n_days, 0.0, R, rng)
        print(f"{n_days:>14} | {fp_indep:>10.1%} | {fp_corr:>12.1%} | "
              f"{fp_one:>9.1%} | {best_sh:>14.2f}")

    print("-" * 78)
    print("\nHOW MANY CONTESTANTS THE ARENA CAN AFFORD (at min_days_on_rung):")
    print("-" * 78)
    for k in (1, 5, 10, 26, 40):
        fp, _ = false_positive_rate(k, R["min_days_on_rung"], 0.5, R, rng)
        print(f"  K={k:>3} contestants (corr 0.5): false-positive rate {fp:>6.1%}")

    print("\nRead the writeup in docs/research/ for what this means and what it")
    print("does NOT mean. This script changes nothing and decides nothing.")


def _norm_cdf(x):
    """Standard normal CDF via erf -- avoids a scipy dependency."""
    import math
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


if __name__ == "__main__":
    main()
