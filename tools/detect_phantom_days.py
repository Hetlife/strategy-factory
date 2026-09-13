"""
Detect PHANTOM TRADING DAYS in the recorded evidence.

WHAT A PHANTOM DAY IS: factory.py's fetch_prices() ends with
`px.dropna(how="all").ffill()`. `dropna(how="all")` only removes a date
row where EVERY ticker is missing. So if Yahoo returns a row where most
tickers are NaN -- an NSE holiday it still lists, or a day whose data
hasn't posted yet -- that row survives, and `.ffill()` fills every
missing ticker with YESTERDAY'S CLOSE. The result is a recorded "trading
day" on which essentially every stock closed exactly unchanged, which
does not happen in a real market.

WHY IT MATTERS (measured, not assumed -- see the 2026-09-13 finding in
bug_log.md): update() increments `days_on_rung` unconditionally, so a
phantom day advances the 126-day promotion clock without any real
evidence behind it. It also adds a paired day to the benchmark
comparison, which LOWERS the multiplicity Sharpe floor (the floor scales
as sqrt(252/n), so more days = easier bar). Both of those push in the
UNSAFE direction -- promotion becomes easier on days the market never
traded. (Sharpe itself moves the other way: extra 0.0 days shrink the
mean faster than the standard deviation, so Sharpe is deflated, which is
conservative. The net effect is mixed, which is exactly why this reports
the evidence rather than asserting a single direction.)

HOW IT DETECTS: factory_state/market_log.json records every ticker's
close and return for each day update() ran -- an independent record of
what the market did, separate from any strategy's own history. A day
where >= PHANTOM_THRESHOLD of tickers show EXACTLY 0.0 return is flagged.
A real trading day has a handful of unchanged illiquid names at most.

Read-only. Needs no network -- market_log.json is in the repo. Prints
findings, writes nothing, changes nothing.

USAGE: python tools/detect_phantom_days.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import factory

# A real NSE day has a few unchanged illiquid names; it never has 80% of
# the Nifty 100 closing at exactly the previous close. Deliberately set
# well above any plausible real day so a flag is unambiguous rather than
# a judgment call.
PHANTOM_THRESHOLD = 0.80
MIN_TICKERS_TO_JUDGE = 10


def classify(log):
    """(phantom, real, unjudgeable) lists of (date, zero_frac, n_tickers)."""
    phantom, real, unjudgeable = [], [], []
    for date in sorted(log):
        day = log[date]
        if not isinstance(day, dict):
            continue
        rows = [v for v in day.values()
                if isinstance(v, dict) and "ret" in v]
        n = len(rows)
        if n < MIN_TICKERS_TO_JUDGE:
            unjudgeable.append((date, None, n))
            continue
        zeros = sum(1 for v in rows if v["ret"] == 0.0)
        frac = zeros / n
        (phantom if frac >= PHANTOM_THRESHOLD else real).append((date, frac, n))
    return phantom, real, unjudgeable


def main():
    log = factory.load_json(factory.MARKET_LOG_PATH, {})
    if not log:
        print("market_log.json is empty or missing -- nothing to check.")
        print("NOTE: market_log.json is only committed to main by "
              "factory.yml. A feature-branch checkout sees a stale copy; "
              "re-run against main for the current record.")
        return

    phantom, real, unjudgeable = classify(log)
    dates = sorted(log)
    print(f"market_log.json: {len(log)} recorded day(s), "
          f"{dates[0]} -> {dates[-1]}\n")

    print(f"PHANTOM (>= {PHANTOM_THRESHOLD:.0%} of tickers exactly 0.0 "
          f"-- not a real trading day):")
    if phantom:
        for d, frac, n in phantom:
            print(f"   {d}   {frac:.0%} of {n} tickers unchanged")
    else:
        print("   none found")

    print(f"\nREAL (normal dispersion):")
    for d, frac, n in real:
        print(f"   {d}   {frac:.0%} of {n} tickers unchanged")

    if unjudgeable:
        print(f"\nTOO FEW TICKERS TO JUDGE (< {MIN_TICKERS_TO_JUDGE}):")
        for d, _, n in unjudgeable:
            print(f"   {d}   only {n} ticker(s) recorded")

    judged = len(phantom) + len(real)
    print("\n" + "=" * 70)
    if judged:
        print(f"VERDICT: {len(phantom)} of {judged} judgeable day(s) are "
              f"phantom ({len(phantom)/judged:.0%}).")
    if phantom:
        print("Each phantom day advanced every contestant's days_on_rung by 1 "
              "and added a paired benchmark day, without any real market "
              "activity behind it.")
        print("\nNOT FIXED HERE. The fix (skip recording when the panel "
              "hasn't actually advanced) changes what data the promotion "
              "gate sees, so it needs Het's explicit authorization -- same "
              "category as the 2026-09-13 rounding fix. This tool only "
              "measures the problem.")
    print("\nCAVEAT ON COVERAGE: market_log.json only starts when "
          "append_market_log() was added, which is LATER than the "
          "contestants' own history. Days before that cannot be checked "
          "this way -- the true phantom count over the full evidence "
          "window is unknown and is very likely higher than what this "
          "prints.")


if __name__ == "__main__":
    main()
