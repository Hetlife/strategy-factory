"""
Answers EXECUTION_PLAN.md Section 8's Q4:

  "Does any contestant beat the Nifty benchmark net of real cost and tax?"

This is the Phase 1 -> Phase 2 gate question. It is a MEASUREMENT, not a
decision: it changes no thresholds and promotes nobody.

WHAT IS ALREADY ACCOUNTED FOR, AND WHAT THIS ADDS
-------------------------------------------------
Cost: already baked in. factory.update() stores each daily return as
`net = day_ret - round_trip_cost(...)` (factory.py ~line 550), using the
size-aware cost model (variable STT/exchange/stamp/GST + the FIXED
Rs 15.34 DP charge per scrip per sell-day). So every return read here is
ALREADY net of realistic Indian delivery costs.

Tax: NOT in the stored returns. Added here via factory.post_tax_expectancy(),
which classifies a contestant by average holding period against the 12-month
STCG/LTCG boundary (20% vs 12.5%).

The tax layer is where an important asymmetry lives, and it works AGAINST
active trading: a buy-and-hold index position eventually pays LTCG (12.5%),
while a strategy that turns over inside 12 months pays STCG (20%). A
strategy must out-earn the index by enough to cover that gap before it is
worth running at all.

WHY THE ANSWER IS PROBABLY "NOT YET, AND HERE IS HOW FAR OFF WE ARE"
--------------------------------------------------------------------
Q5 (docs/research/Q5_statistical_power.md) established that at this
sample size the noise dwarfs any plausible edge. This script therefore
reports, for every contestant, not just the point estimate but the
CONFIDENCE INTERVAL and the sample size that would actually be needed to
call the observed gap real. A point estimate without that is exactly the
kind of number this project exists not to fool itself with.

Read-only. Fetches the LIVE ledger from main. Writes nothing. Reuses
factory.py's own functions so it cannot drift from live behaviour.

USAGE: python3 tools/analyze_q4_vs_benchmark.py
"""
import os
import sys
import math

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import factory
from tools.health_check import fetch_live_json

TRADING_DAYS = factory.TRADING_DAYS_PER_YEAR


def paired_excess(hist, bench_map):
    """Date-paired daily excess returns vs the benchmark. Same pairing the
    live promotion gate uses -- day by day, so the shared market move
    cancels instead of being compared across mismatched dates."""
    return [row[1] - bench_map[row[0]] for row in hist if row[0] in bench_map]


def stats(xs):
    n = len(xs)
    if n < 2:
        return n, float("nan"), float("nan"), float("nan")
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)
    return n, mean, sd, se


def days_needed(mean, sd, z=1.96):
    """How many paired days it would take for an edge of the observed size
    to become statistically distinguishable from zero. Honest framing of
    'when would we actually know', rather than a verdict now."""
    if mean <= 0 or sd <= 0 or math.isnan(mean) or math.isnan(sd):
        return None
    return math.ceil((z * sd / mean) ** 2)


def main():
    print("Q4 — DOES ANY CONTESTANT BEAT NIFTY, NET OF REAL COST AND TAX?")
    print("=" * 78)

    state = fetch_live_json("factory_state/ledger.json")
    reg, con = state["registry"], state["contestants"]

    bench_name = next((n for n in con
                       if reg.get(n, {}).get("permanent")), None)
    if not bench_name:
        print("No benchmark contestant found. Cannot answer Q4.")
        return
    bench = con[bench_name]
    bench_map = {r[0]: r[1] for r in bench["history"]}
    bn = max(bench["days_in_market"], 1)
    bench_mean = bench["sum_ret"] / bn
    bench_post_tax, bench_basis = factory.post_tax_expectancy(
        bench_mean, bench["days_in_market"], bench["trades"])

    print(f"Benchmark: {bench_name}  ({bench['days_in_market']} days in market, "
          f"{bench['trades']} trades)")
    print(f"  mean daily return (net of cost): {bench_mean:+.6f}")
    print(f"  annualised                     : {bench_mean*TRADING_DAYS:+.2%}")
    print(f"  tax basis as classified        : {bench_basis} "
          f"-> post-tax daily {bench_post_tax:+.6f}")
    if bench_basis == "STCG":
        ltcg_mean = bench_mean * (1 - factory.LTCG_RATE)
        print(f"  NOTE: classified STCG only because the window is still short "
              f"({bench['days_in_market']}d / {bench['trades']} trades < "
              f"{TRADING_DAYS}).")
        print(f"        A real buy-and-hold index position pays LTCG "
              f"({factory.LTCG_RATE:.1%}) -> {ltcg_mean:+.6f}. Active "
              f"strategies pay STCG ({factory.STCG_RATE:.1%}).")
        print(f"        That gap is a real headwind active trading must clear.")

    rows = []
    for name, s in con.items():
        if s["retired"] or name == bench_name:
            continue
        ex = paired_excess(s.get("history", []), bench_map)
        n, mean, sd, se = stats(ex)
        n_days = max(s["days_in_market"], 1)
        own_mean = s["sum_ret"] / n_days
        pt_mean, basis = factory.post_tax_expectancy(
            own_mean, s["days_in_market"], s["trades"])
        # Tax applies to gains. For a losing strategy the model's
        # multiplication would flatter it, so report it as not applicable.
        pt_excess = (pt_mean - bench_post_tax) if own_mean > 0 else float("nan")
        rows.append(dict(name=name, n=n, mean=mean, sd=sd, se=se,
                         own_mean=own_mean, pt_mean=pt_mean, basis=basis,
                         pt_excess=pt_excess, trades=s["trades"],
                         days=s["days_in_market"]))

    rows.sort(key=lambda r: (-r["mean"]) if not math.isnan(r["mean"]) else 1e9)

    print(f"\nContestants measured: {len(rows)} (excluding the benchmark and "
          f"retired entries)\n")
    print("PRE-TAX EXCESS vs BENCHMARK (daily, date-paired, already net of cost)")
    print("-" * 78)
    print(f"{'contestant':<26} {'n':>4} {'excess/day':>11} {'95% CI':>22} {'beats?':>8}")
    print("-" * 78)

    beats_gross = 0
    for r in rows:
        if math.isnan(r["mean"]):
            print(f"{r['name']:<26} {r['n']:>4} {'insufficient data':>11}")
            continue
        lo = r["mean"] - 1.96 * r["se"]
        hi = r["mean"] + 1.96 * r["se"]
        ci = f"[{lo:+.5f}, {hi:+.5f}]"
        # "Beats" means the ENTIRE interval is above zero, not just the
        # point estimate. A positive point estimate with an interval
        # straddling zero is not evidence of an edge.
        verdict = "YES" if lo > 0 else ("(pos)" if r["mean"] > 0 else "no")
        if lo > 0:
            beats_gross += 1
        print(f"{r['name']:<26} {r['n']:>4} {r['mean']:>+11.5f} {ci:>22} {verdict:>8}")

    print("-" * 78)
    print(f"Contestants beating the benchmark with 95% confidence: {beats_gross}")
    print('"(pos)" = positive point estimate but the confidence interval')
    print("        includes zero -- i.e. indistinguishable from luck.")

    print("\n\nPOST-TAX (the comparison that actually decides Phase 1 -> 2)")
    print("-" * 78)
    print(f"{'contestant':<26} {'basis':>6} {'own post-tax':>13} "
          f"{'vs bench':>11} {'ahead?':>7}")
    print("-" * 78)
    beats_net = 0
    for r in rows:
        if math.isnan(r["pt_excess"]):
            print(f"{r['name']:<26} {r['basis']:>6} {r['pt_mean']:>+13.6f} "
                  f"{'n/a (losing)':>11} {'no':>7}")
            continue
        ahead = "YES" if r["pt_excess"] > 0 else "no"
        if r["pt_excess"] > 0:
            beats_net += 1
        print(f"{r['name']:<26} {r['basis']:>6} {r['pt_mean']:>+13.6f} "
              f"{r['pt_excess']:>+11.6f} {ahead:>7}")
    print("-" * 78)
    print(f"Ahead of the benchmark on post-tax point estimate: {beats_net}")
    print("(Point estimate only -- see the confidence intervals above before")
    print(" reading anything into it.)")

    print("\n\nHOW LONG UNTIL WE COULD ACTUALLY TELL?")
    print("-" * 78)
    print("For contestants with a positive excess, the paired-day count that")
    print("would make an edge THAT SIZE distinguishable from zero at 95%:")
    print("-" * 78)
    any_shown = False
    for r in rows:
        if math.isnan(r["mean"]) or r["mean"] <= 0:
            continue
        need = days_needed(r["mean"], r["sd"])
        if need is None:
            continue
        any_shown = True
        yrs = need / TRADING_DAYS
        print(f"  {r['name']:<26} has {r['n']:>4} paired days, "
              f"would need ~{need:>6} ({yrs:>5.1f} trading yrs)")
    if not any_shown:
        print("  None -- no contestant currently shows a positive excess.")

    print("\n" + "=" * 78)
    print("EVIDENCE LEVEL: 6 (paper / shadow execution on real prices).")
    print("These are PAPER results on real market data, net of a realistic")
    print("cost model. They are NOT realized profit and no money is at risk.")
    print("Read docs/research/Q4_beat_nifty.md for the interpretation.")


if __name__ == "__main__":
    main()
