"""
One-off diagnostic: is the event_drift family's 0-trades pattern expected
(genuinely rare real-world moves) or a parameter/logic bug? Also reports
percentile stats over a full year, so a threshold change (if Het wants
one) can be an informed choice against real volatility, not a guess.

Origin: Het noticed most contestants show 0 trades on his hosted dashboard
(2026-08-27). Checked: event_cement/infra/steel_t30/t40/t50 (6 of 23
contestants) and monsoon_cement all show days_on_rung=38, trades=0.
monsoon_cement is CONFIRMED intentional (sig_monsoon is a documented
dormant no-op, its registry csv path doesn't even match the real sourced
file -- deliberate, not a bug, data ends 2017). event_drift is the real
open question: does its leader ticker (ULTRACEMCO.NS / LT.NS / the steel
leader) ever actually cross the 3%/4%/5% single-day threshold in real
recent history, or is the threshold/logic simply never satisfiable?

2026-08-28 update: Het asked "how do we make them trade more" -- added a
percentile breakdown (95th/90th/85th/80th) over a full trading year so
any threshold change is an informed, principled choice (still Het's
call, this script only reports, never changes seed_registry() itself).

This sandbox can't reach Yahoo Finance (documented env fact) -- this
script is meant to run on a GitHub Actions runner, which can. Read-only,
prints findings, writes/commits nothing.

USAGE: python tools/diagnose_event_thresholds.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import numpy as np
import factory


def main():
    reg = factory.seed_registry()
    event_entries = {k: v for k, v in reg.items() if v.get("fn") == "event_drift"}
    leaders = sorted({v["leader"] for v in event_entries.values()})

    print(f"Checking {len(leaders)} leader ticker(s) used by "
          f"{len(event_entries)} event_drift contestant(s): {leaders}\n")

    px = factory.fetch_prices()
    for leader in leaders:
        if leader not in px.columns:
            print(f"[{leader}] NOT in fetched price panel -- can't check, "
                  f"this itself may be the real bug.")
            continue
        rets = px[leader].pct_change().dropna()
        recent = rets.iloc[-60:]  # ~last 3 trading months
        year = rets.iloc[-252:]  # ~1 trading year, for percentile context
        max_abs = recent.abs().max()
        n_days = len(recent)
        print(f"[{leader}] {n_days} recent trading days -- "
              f"max |single-day return| = {max_abs:.4f} ({max_abs*100:.2f}%)")
        thresholds_used = sorted({v["threshold"] for v in event_entries.values()
                                   if v["leader"] == leader})
        for thr in thresholds_used:
            n_hits = int((recent.abs() > thr).sum())
            print(f"    threshold {thr:.3f} ({thr*100:.1f}%): "
                  f"{n_hits} day(s) in the last {n_days} would have crossed it")

        yr_abs = year.abs()
        print(f"    -- over the last {len(year)} trading days (~1yr), "
              f"|daily return| percentiles:")
        for pct in (95, 90, 85, 80):
            v = np.percentile(yr_abs, pct)
            implied_hits_per_year = len(year) * (100 - pct) / 100
            print(f"       {pct}th pct = {v*100:.2f}% "
                  f"(a threshold here fires ~{implied_hits_per_year:.0f}x/yr "
                  f"by construction)")

    print("\nConclusion guide: if max |return| never gets close to the "
          "smallest threshold (t30, 3%) across a real recent window, the "
          "threshold is likely just genuinely too high for these tickers' "
          "real volatility -- worth flagging to Het as a parameter question, "
          "NOT silently changing (LADDER/RULES-adjacent judgment call, "
          "needs his input). If moves DID cross the threshold but the "
          "contestant still shows 0 trades, that points to an actual logic "
          "bug in sig_event_drift() or how update() calls it -- worth a "
          "real fix, not just a parameter tweak. The percentile breakdown "
          "above answers 'what threshold would fire N times/year' honestly "
          "-- it does NOT recommend a number; picking one that changes the "
          "actual real-world-shock definition is Het's call, not something "
          "to reverse-engineer from a target trade count (that would be "
          "exactly the Law 1 mining pattern this project exists to avoid).")


if __name__ == "__main__":
    main()
