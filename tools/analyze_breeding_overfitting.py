"""
Answers EXECUTION_PLAN.md Section 8's Q6:

  "Does the 3-mechanism evolution system (spawn/advisor/crossover)
   increase overfitting risk vs. a simpler design at this sample size?
   Should any mechanism be disabled during Phase 1?"

Companion to tools/analyze_statistical_power.py (Q5). Same method: an
explicit zero-edge null, calibrated to the project's own real measured
daily volatility, run through factory.py's real eligibility logic.

THE SPECIFIC THING THIS TESTS: breeding selects parents by "is it
profitable, and has it traded enough?" If, at the sample sizes where
breeding can actually fire, a coin-flip contestant looks profitable
about as often as a skilled one, then breeding is selecting luck and
propagating it into children -- which is overfitting with extra steps.

Read alongside docs/research/Q6_breeding_overfitting.md.

Read-only. Reads real thresholds from factory.py so it cannot drift.
Seeded and deterministic. Changes nothing.

USAGE: python3 tools/analyze_breeding_overfitting.py
"""
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import factory

REAL_DAILY_VOL = 0.01119        # measured from the live ledger, see Q5
N_TRIALS = 20000
SEED = 11


def sim_equity_paths(k, n_days, vol, rng, weekly_tax):
    """Simulate k zero-edge contestants for n_days, returning final equity
    the way factory.py compounds it, including the paper holding-cost
    decay that report() applies to rung-0 contestants each weekly round.
    """
    r = rng.standard_normal((n_days, k)) * vol
    equity = np.prod(1.0 + r, axis=0)
    # report() runs weekly; rung-0 non-permanent contestants get taxed each round
    weeks = n_days / 5.0
    equity *= (1.0 - weekly_tax) ** weeks
    return equity


def main():
    R = factory.RULES
    tax = getattr(factory, "PAPER_HOLDING_TAX_WEEKLY", 0.0013)
    rng = np.random.default_rng(SEED)

    print("Q6 — DOES BREEDING SELECT SKILL, OR LUCK, AT THIS SAMPLE SIZE?")
    print("=" * 74)
    print("Null hypothesis: NO contestant has any edge. All returns are noise.")
    print(f"Real measured daily vol: {REAL_DAILY_VOL}")
    print(f"PAPER_HOLDING_TAX_WEEKLY: {tax}")
    print(f"BREEDING_TOP_N={factory.BREEDING_TOP_N}  "
          f"BREEDING_MIN_TRADES={factory.BREEDING_MIN_TRADES}  "
          f"BREEDING_MAX_NEW_PER_ROUND={factory.BREEDING_MAX_NEW_PER_ROUND}")
    print(f"MAX_CONTESTANTS={factory.MAX_CONTESTANTS}\n")

    print("CROSSOVER ELIGIBILITY GATE IS 'equity > 1.0' (profitable).")
    print("Under the null, how often does a PURE-NOISE contestant look profitable?\n")
    print(f"{'days':>8} | {'P(equity>1.0 | zero edge)':>26} | {'reads as'}")
    print("-" * 74)
    for n_days in (20, 40, 63, 126, 252, 504, 756):
        eq = sim_equity_paths(N_TRIALS, n_days, REAL_DAILY_VOL, rng, tax)
        p = float((eq > 1.0).mean())
        verdict = ("indistinguishable from a coin flip" if 0.40 <= p <= 0.60
                   else "weakly informative" if 0.30 <= p <= 0.70
                   else "carries real signal")
        print(f"{n_days:>8} | {p:>25.1%} | {verdict}")

    print("-" * 74)
    print("\nA gate that a zero-edge contestant clears ~half the time is not")
    print("evidence of skill. It is a coin flip that we then breed from.\n")

    # How much does growing the arena cost us, in Q5's terms?
    print("WHAT BREEDING DOES TO THE FALSE-POSITIVE RATE (Q5's measure)")
    print("-" * 74)
    print("Breeding adds up to "
          f"{factory.BREEDING_MAX_NEW_PER_ROUND} contestants per weekly report round,")
    print(f"growing the arena toward MAX_CONTESTANTS={factory.MAX_CONTESTANTS}.")
    print("From Q5 (same null, 126 days, correlation 0.5):")
    print("    26 contestants -> 84.4% chance a pure-noise contestant is PROMOTED")
    print("    40 contestants -> 88.9% chance a pure-noise contestant is PROMOTED")
    print("Every child added is another lottery ticket in the same draw.\n")

    print("CUMULATIVE HYPOTHESES TESTED (the part Q5 did NOT model)")
    print("-" * 74)
    print("Q5 assumed a FIXED set of 26 contestants. Breeding churns the")
    print("population: children are born, stragglers are retired/evolved out.")
    print("The number of DISTINCT hypotheses the tournament tests over its")
    print("life is therefore larger than the number alive at any moment --")
    print("so Q5's false-positive figures are a FLOOR, not a ceiling, once")
    print("breeding is active.\n")
    for weeks in (18, 52):
        max_new = factory.BREEDING_MAX_NEW_PER_ROUND * weeks
        print(f"  Over {weeks:>2} weekly rounds: up to {max_new:>3} additional "
              f"distinct contestants could be born (cap-limited in practice).")

    print("\nSee docs/research/Q6_breeding_overfitting.md for the conclusion,")
    print("the documentation error this uncovered, and what needs Het's call.")


if __name__ == "__main__":
    main()
