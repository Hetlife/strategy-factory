"""
One-off diagnostic: is input_cost_crude_cement/steel's 0-trades pattern
expected (a genuinely rare real-world 20-day Brent crude drop) or is the
-5% threshold simply unrealistic for BZ=F's actual volatility?

Origin: Het's 2026-09-13 request to "loosen the trigger" on the 15
never-traded contestants. Applying the SAME rigor already used for the
event_drift family (tools/diagnose_event_thresholds.py, 2026-08-27/28):
check real historical data first, report percentiles, let a human choose
a threshold informed by real volatility -- never reverse-engineer a
number from a target trade count (that would be exactly the Law 1 data-
mining pattern this project exists to avoid).

Mechanism being checked: sig_input_cost() triggers when BZ=F's cumulative
return over the last `lb` (20) trading days is more negative than `drop`
(-0.05), i.e. a 5%+ crude-oil price drop over one trading month. Checks
the ROLLING 20-day cumulative return (not single-day, unlike event_drift)
against a full year of real BZ=F history.

This sandbox can't reach Yahoo Finance (documented env fact) -- this
script is meant to run on a GitHub Actions runner, which can. Read-only,
prints findings, writes/commits nothing.

USAGE: python tools/diagnose_input_cost_threshold.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import numpy as np
import factory


def main():
    reg = factory.seed_registry()
    ic_entries = {k: v for k, v in reg.items() if v.get("fn") == "input_cost"}
    proxies = sorted({v["proxy"] for v in ic_entries.values()})

    print(f"Checking {len(proxies)} proxy ticker(s) used by "
          f"{len(ic_entries)} input_cost contestant(s): {proxies}\n")

    px = factory.fetch_prices()
    for proxy in proxies:
        if proxy not in px.columns:
            print(f"[{proxy}] NOT in fetched price panel -- can't check, "
                  f"this itself may be the real bug (contestants using it "
                  f"would silently never trade regardless of threshold).")
            continue
        entries_here = {k: v for k, v in ic_entries.items() if v["proxy"] == proxy}
        lbs = sorted({v["lb"] for v in entries_here.values()})
        px_series = px[proxy].dropna()
        year = px_series.iloc[-252:]
        print(f"[{proxy}] {len(year)} trading days of real history "
              f"(last available: {year.index[-1].date()})")

        for lb in lbs:
            roll = year.pct_change(lb).dropna()
            drops_used = sorted({v["drop"] for v in entries_here.values()
                                  if v["lb"] == lb})
            print(f"  {lb}-day rolling cumulative return -- "
                  f"min observed = {roll.min()*100:.2f}%, "
                  f"max observed = {roll.max()*100:.2f}%")
            for drop in drops_used:
                n_hits = int((roll < drop).sum())
                print(f"    threshold {drop:.3f} ({drop*100:.1f}%): "
                      f"{n_hits} day(s) in the last {len(roll)} rolling "
                      f"windows would have crossed it "
                      f"(~{n_hits*252/max(len(roll),1):.1f}x/yr by rate)")
            print(f"    -- percentile context (most-negative tail):")
            for pct in (5, 10, 15, 20):
                v = np.percentile(roll, pct)
                implied_per_year = len(roll) * pct / 100
                print(f"       {pct}th pct = {v*100:.2f}% "
                      f"(a threshold here fires ~{implied_per_year:.0f}x/yr "
                      f"by construction)")

    print("\nConclusion guide: if the -5% threshold sits deep in the tail "
          "(few or zero real crossings in a full year), it's genuinely "
          "rare for this proxy/lookback, not a bug -- worth flagging as a "
          "parameter question, same as the event_drift finding. If real "
          "crossings DID happen but the contestant still shows 0 trades, "
          "that points to an actual logic bug (e.g. ticker not in the "
          "fetched panel), worth a real fix. The percentile breakdown "
          "answers 'what threshold fires N times/year' honestly -- it "
          "does NOT recommend a number; picking one that changes the "
          "real-world-shock definition is Het's call each time, never "
          "reverse-engineered from a target trade count.")


if __name__ == "__main__":
    main()
