"""
BACKFILL nifty_benchmark's missing history from real index data.

THE PROBLEM (Q4 finding, docs/research/Q4_beat_nifty.md): the promotion
gate compares each contestant against nifty_benchmark DATE BY DATE, and
the shorter side caps the usable sample. Contestants' history starts
2026-07-13; nifty_benchmark's starts 2026-08-26, because the benchmark
contestant was added to the ledger later. Result: ~37 of every
contestant's ~43 recorded days cannot be paired, every excess-return
estimate is starved, and the gate fails closed for everyone. The first
possible honest promotion slipped ~6 weeks purely for this reason.

WHY BACKFILLING THIS SPECIFIC THING IS LEGITIMATE (Het's explicit
authorization, 2026-09-13, after the argument was put to him both ways):
nifty_benchmark is buy-and-hold. sig_benchmark() returns
{BENCHMARK: 1.0} unconditionally -- it makes no decisions, has no
parameters, and has no discretion to reconstruct. What the index returned
on any past date is a matter of public record, not a simulation of
choices it might have made. That is categorically different from
backfilling a STRATEGY's history, which would mean inventing trades it
never placed. This tool will refuse to touch anything except
nifty_benchmark, by name.

WHAT IT DELIBERATELY DOES NOT DO:
  * Never modifies an EXISTING history row. Only prepends dates that are
    genuinely absent. Observed-live data stays exactly as observed --
    including the small initial-purchase cost recorded on 2026-08-26,
    which is left alone rather than rewritten to look tidier.
  * Never backfills a date the real index has no data for. On an NSE
    holiday there is no real return to record, so that date simply stays
    unpaired -- which is the honest outcome, and it automatically keeps
    the phantom trading days (see tools/detect_phantom_days.py) OUT of
    the paired comparison.
  * Never touches days_on_rung. That is a promotion clock, the benchmark
    is permanent and never promotes, so inflating it would be
    meaningless.
  * Never touches RULES, LADDER, COST_PER_SIDE, or any registry entry.

DRY RUN BY DEFAULT. It prints exactly what it would change and exits.
Pass --apply to write, which also takes a timestamped backup of
ledger.json first.

This sandbox cannot reach market data (yfinance blocked, verified
2026-09-13), so --apply is meant to run on a GitHub Actions runner.

USAGE:
    python tools/backfill_benchmark_history.py            # dry run
    python tools/backfill_benchmark_history.py --apply    # write
"""
import os
import shutil
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import math

import factory

BENCHMARK_KEY = "nifty_benchmark"     # the ONLY contestant this may touch


def fetch_index_history(period="1y"):
    """Real daily closes for the benchmark index only, as a Series.

    yfinance returns a DataFrame from ["Close"] even for a SINGLE ticker
    (one column, named for the ticker) -- unlike factory.fetch_prices(),
    which passes a LIST and genuinely wants the ticker-columned frame.
    Squeezing here rather than assuming a Series: the first real run of
    this tool died on exactly that (TypeError: cannot convert the series
    to <class 'float'>), caught harmlessly because dry run writes
    nothing. Handle both shapes so a future yfinance change can't
    reintroduce it."""
    import pandas as pd
    import yfinance as yf
    px = yf.download(factory.BENCHMARK, period=period, auto_adjust=True,
                     progress=False)["Close"]
    if isinstance(px, pd.DataFrame):
        if factory.BENCHMARK in px.columns:
            px = px[factory.BENCHMARK]
        elif px.shape[1] == 1:
            px = px.iloc[:, 0]
        else:
            raise ValueError(
                f"expected one close series for {factory.BENCHMARK}, got "
                f"columns {list(px.columns)} -- refusing to guess")
    return px.dropna()


def missing_dates(state):
    """Dates some contestant recorded but the benchmark did not."""
    con = state["contestants"]
    bench = con.get(BENCHMARK_KEY)
    if bench is None:
        return None, None, None
    have = {r[0] for r in bench["history"]}
    wanted = set()
    for name, s in con.items():
        if name == BENCHMARK_KEY:
            continue
        wanted.update(r[0] for r in s.get("history", []))
    return sorted(wanted - have), sorted(have), sorted(wanted)


def main():
    apply_changes = "--apply" in sys.argv
    state = factory.load_state()
    con = state["contestants"]

    gaps, have, wanted = missing_dates(state)
    if gaps is None:
        print(f"[FATAL] {BENCHMARK_KEY} not found in the ledger. Stopping.")
        return
    bench = con[BENCHMARK_KEY]
    print(f"{BENCHMARK_KEY}: {len(have)} recorded day(s)"
          + (f", {have[0]} -> {have[-1]}" if have else " (none)"))
    print(f"contestants collectively cover {len(wanted)} day(s)"
          + (f", {wanted[0]} -> {wanted[-1]}" if wanted else ""))
    print(f"UNPAIRED (contestant days the benchmark cannot match): "
          f"{len(gaps)}\n")
    if not gaps:
        print("Nothing to backfill -- the benchmark already covers every "
              "date any contestant has. Exiting without changes.")
        return

    px = fetch_index_history()
    rets = px.pct_change()
    index_by_date = {str(d.date()): float(r)
                     for d, r in rets.items() if not math.isnan(r)}
    print(f"Real {factory.BENCHMARK} history fetched: {len(px)} closes, "
          f"{str(px.index[0].date())} -> {str(px.index[-1].date())}")

    fillable = [d for d in gaps if d in index_by_date]
    unfillable = [d for d in gaps if d not in index_by_date]
    print(f"  of the {len(gaps)} unpaired dates, {len(fillable)} have real "
          f"index data and {len(unfillable)} do not")
    if unfillable:
        print(f"  NOT filling (no real index data -- almost certainly NSE "
              f"holidays or phantom days): {', '.join(unfillable[:8])}"
              + (" ..." if len(unfillable) > 8 else ""))
    if not fillable:
        print("\nNothing fillable. Exiting without changes.")
        return

    # Build the prepended rows. Equity compounds from 1.0 across the
    # backfilled stretch only; existing rows keep their own original
    # basis and are never rewritten (see module docstring).
    equity = 1.0
    new_rows, total, total_sq = [], 0.0, 0.0
    for d in fillable:
        r = index_by_date[d]
        equity *= (1 + r)
        new_rows.append([d, round(r, 6), round(equity, 5)])
        total += r
        total_sq += r * r

    print(f"\nWOULD PREPEND {len(new_rows)} row(s): "
          f"{new_rows[0][0]} -> {new_rows[-1][0]}")
    print(f"  first: {new_rows[0]}")
    print(f"  last:  {new_rows[-1]}")
    print(f"  index return over the backfilled stretch: "
          f"{(equity - 1) * 100:+.2f}%")
    print(f"\nWOULD UPDATE {BENCHMARK_KEY} aggregates:")
    print(f"  history rows : {len(bench['history'])} -> "
          f"{len(bench['history']) + len(new_rows)}")
    print(f"  days_in_market: {bench['days_in_market']} -> "
          f"{bench['days_in_market'] + len(new_rows)}")
    print(f"  sum_ret       : {bench['sum_ret']:.6f} -> "
          f"{bench['sum_ret'] + total:.6f}")
    print("  days_on_rung / equity / peak / positions / trades: UNCHANGED "
          "(see module docstring)")
    print(f"\nWOULD NOT TOUCH: {len(con) - 1} other contestant(s), the "
          f"registry, RULES, LADDER, or COST_PER_SIDE.")

    # How much this actually buys, in gate terms.
    paired_before = len(set(have))
    paired_after = paired_before + len(new_rows)
    def floor(n):
        from statistics import NormalDist
        k = sum(1 for n_, c in con.items()
                if not c["retired"]
                and not state["registry"].get(n_, {}).get("permanent"))
        if n < factory.MIN_SHARPE_SAMPLE_DAYS or k < 1:
            return float("inf")
        return (NormalDist().inv_cdf(1 - factory.RULES.get("promotion_alpha", 0.05) / k)
                * math.sqrt(252.0 / n))
    print(f"\nEFFECT ON THE GATE: benchmark-paired days "
          f"{paired_before} -> {paired_after}; multiplicity Sharpe floor "
          f"{floor(paired_before)} -> {floor(paired_after):.3f}")
    print("(a floor of 'inf' means the gate cannot certify anyone at all -- "
          "which is exactly the block this backfill removes)")

    if not apply_changes:
        print("\n" + "=" * 66)
        print("DRY RUN -- nothing was written. Re-run with --apply to "
              "commit these changes.")
        return

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ledger = os.path.join(factory.STATE_DIR, "ledger.json")
    backup = os.path.join(factory.STATE_DIR, f"ledger.backup.{stamp}.json")
    shutil.copy2(ledger, backup)
    print(f"\nBackup written: {backup}")

    before_others = {n: len(s.get("history", []))
                     for n, s in con.items() if n != BENCHMARK_KEY}
    merged = new_rows + bench["history"]
    dates_seen = [r[0] for r in merged]
    # The EXISTING history may already contain duplicate dates -- it does,
    # in production: factory.yml's update step has no weekday guard, so it
    # also runs on the Sunday report cron, when the price panel's newest
    # row is still Friday's, and Friday gets appended a second time (see
    # bug_log.md 2026-09-13, ledger-duplicate-trading-days). That is a
    # pre-existing defect this tool must neither inherit nor paper over:
    # assert only that WE introduce no new collision, and leave the
    # existing rows exactly as recorded.
    new_dates = [r[0] for r in new_rows]
    assert len(new_dates) == len(set(new_dates)), \
        "backfill would introduce duplicate dates -- aborting"
    assert not (set(new_dates) & {r[0] for r in bench["history"]}), \
        "backfill would collide with an existing date -- aborting"
    assert new_dates == sorted(new_dates), \
        "backfilled dates out of order -- aborting"
    pre_existing_dupes = len(dates_seen) - len(set(dates_seen))
    if pre_existing_dupes:
        print(f"\n[NOTE] the benchmark's existing history already carries "
              f"{pre_existing_dupes} duplicate date row(s), pre-dating this "
              f"backfill. Left exactly as recorded -- cleaning them is a "
              f"separate decision. excess_return_stats() already dedupes by "
              f"date, so the promotion gate is unaffected.")
    bench["history"] = merged
    bench["days_in_market"] += len(new_rows)
    bench["sum_ret"] += total
    bench["sum_sq"] += total_sq
    factory.save_state(state)

    # Verify what we actually wrote, from disk, rather than trusting memory.
    check = factory.load_state()
    cb = check["contestants"][BENCHMARK_KEY]
    after_others = {n: len(s.get("history", []))
                    for n, s in check["contestants"].items()
                    if n != BENCHMARK_KEY}
    assert after_others == before_others, \
        "another contestant's history changed -- restore from the backup"
    print(f"VERIFIED on reload: {BENCHMARK_KEY} now has "
          f"{len(cb['history'])} rows, {cb['history'][0][0]} -> "
          f"{cb['history'][-1][0]}; every other contestant unchanged.")
    print("\nApplied.")


if __name__ == "__main__":
    main()
