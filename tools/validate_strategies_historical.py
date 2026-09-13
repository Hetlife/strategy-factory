"""
HISTORICAL VALIDATION: would each live strategy EVER have cleared the real
promotion bar, across ~5 years of real market history?

WHY THIS EXISTS (Het, 2026-09-13: "I want to accelerate progress and make
sure that we are not waiting for it to fail but working towards something
real"): the live arena accumulates evidence one calendar day at a time, so
a verdict on any single strategy is months away. But the strategies are
already written down and locked, and the promotion bar is already written
down and locked. Running locked strategies through a locked bar on history
they have never been tuned against is legitimate out-of-sample testing,
not data mining -- and it returns an answer in minutes instead of months.
This is MASTER_PLAN.md's STEP 4 ("out-of-sample before any capital")
pulled forward, not new machinery.

THE ONE RULE THAT KEEPS THIS HONEST -- USE IT TO KILL, NEVER TO PROMOTE:
  * A strategy that NEVER cleared the bar in 5 years of real history is
    strong evidence AGAINST that mechanism. Retiring it is a real,
    defensible decision, and it directly helps every surviving strategy:
    the multiplicity correction means each extra contestant raises the
    Sharpe floor for all the others (measured 2026-09-13: dropping the
    arena from 25 to 10 lowers the floor 10.5% and cuts days-to-certify
    by ~20%).
  * A strategy that DID clear the bar historically has NOT earned
    anything. Backtests flatter: today's index membership is not the
    past's (survivorship bias), and any historical result is one draw
    from a distribution. Live forward evidence is still the only thing
    that promotes. This script deliberately prints no "promote"
    recommendation of any kind.

NO LOOKAHEAD: reuses advisors.backtest() rather than reimplementing the
walk, so the simulated day-by-day ordering, turnover and cost model are
literally the same code paths advisors.py already runs -- the exact class
of drift that bit agents/judge/judge.py before it was made to delegate to
factory.promotion_check(). The promotion test itself calls the REAL
factory.promotion_check(), not a copy.

WEEKLY CHECKPOINTS: factory.report() only evaluates promotion once a week,
so this checks weekly too -- matching how a real promotion could actually
have occurred rather than granting the backtest more chances than live
trading gets.

This sandbox cannot reach any market data source (yfinance blocked, FRED
blocked -- both verified 2026-09-13), so this is built to run on a GitHub
Actions runner. Read-only: writes nothing, touches no ledger, retires
nothing. It only prints evidence for a human to act on.

USAGE: python tools/validate_strategies_historical.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import math

import numpy as np
import pandas as pd

import factory
import advisors

WARMUP = 130          # same warmup advisors.backtest() defaults to
CHECK_EVERY = 5       # trading days between promotion checks (report() is weekly)


def simulate_benchmark(px):
    """{date_str: daily_return} for buy-and-hold BENCHMARK, the same thing
    sig_benchmark() holds live. Built from the same price panel every
    strategy is walked against, so the pairing is apples-to-apples."""
    if factory.BENCHMARK not in px.columns:
        return {}
    rets = px[factory.BENCHMARK].pct_change()
    return {str(d.date()): float(r)
            for d, r in rets.iloc[WARMUP:].items() if not math.isnan(r)}


def walk_with_dates(px, params):
    """advisors.backtest() with the dates put back on. Returns
    (list of (date_str, net_return), n_trades)."""
    net, n_trades = advisors.backtest(px, params, warmup=WARMUP)
    dates = [str(d.date()) for d in px.index[WARMUP:]]
    return list(zip(dates, [float(x) for x in net])), n_trades


def build_state(rows_so_far, n_trades_so_far):
    """A contestant state dict shaped exactly as promotion_check() expects,
    reconstructed from the simulated returns up to this checkpoint."""
    equity, peak = 1.0, 1.0
    hist, sum_ret, sum_sq = [], 0.0, 0.0
    for date, net in rows_so_far:
        equity *= (1 + net)
        peak = max(peak, equity)
        sum_ret += net
        sum_sq += net * net
        hist.append([date, round(net, 6), round(equity, 5)])
    n = max(len(rows_so_far), 1)
    mean = sum_ret / n
    if n < factory.MIN_SHARPE_SAMPLE_DAYS:
        sharpe = float("nan")
    else:
        var = max(sum_sq / n - mean ** 2, 1e-12)
        sharpe = mean / math.sqrt(var) * math.sqrt(252)
    return dict(rung=0, days_on_rung=len(rows_so_far), trades=n_trades_so_far,
                equity=equity, peak=peak, history=hist), mean, sharpe


def main():
    R = factory.RULES
    state = factory.load_state()
    reg, con = state["registry"], state["contestants"]
    live = {n: p for n, p in reg.items()
            if not p.get("permanent") and not con.get(n, {}).get("retired")}
    n_tests = len(live)

    print(f"Validating {n_tests} live strategies against "
          f"{advisors.TRAIN_PERIOD} of real history.")
    print(f"Promotion bar in force: min_days_on_rung="
          f"{R['min_days_on_rung']}, min_trades={R['min_trades']}, "
          f"min_expectancy={R['min_expectancy']}, "
          f"min_sharpe={R['min_sharpe']}, max_drawdown={R['max_drawdown']}, "
          f"require_beat_benchmark={R.get('require_beat_benchmark')}, "
          f"alpha={R.get('promotion_alpha')}, K={n_tests}\n")

    px = advisors.fetch_history()
    print(f"History: {len(px)} rows, {px.index[0].date()} -> "
          f"{px.index[-1].date()}, {len(px.columns)} tickers")
    bench_map = simulate_benchmark(px)
    print(f"Benchmark ({factory.BENCHMARK}) simulated over "
          f"{len(bench_map)} days\n")
    if not bench_map:
        print("[FATAL] benchmark not in the price panel -- every promotion "
              "check would fail closed and this whole run would be "
              "meaningless. Stopping rather than printing a misleading "
              "table of zeros.")
        return

    usable = len(px) - WARMUP
    if usable < R["min_days_on_rung"] + CHECK_EVERY:
        print(f"[FATAL] only {usable} usable days after warmup, need at "
              f"least {R['min_days_on_rung']}. Stopping.")
        return

    results = []
    for name, params in sorted(live.items()):
        try:
            rows, n_trades = walk_with_dates(px, params)
        except Exception as e:
            results.append(dict(name=name, error=str(e)[:60]))
            print(f"  [warn] {name}: {e}")
            continue

        ever_passed, first_pass_day, best_sharpe = False, None, float("-inf")
        # Trade count accrues over the walk; approximate per-checkpoint
        # trades by pro-rating, which is conservative early on (fewer
        # trades than the full-period count) and exact at the end.
        for end in range(R["min_days_on_rung"], len(rows) + 1, CHECK_EVERY):
            window = rows[:end]
            trades_by_now = int(round(n_trades * end / max(len(rows), 1)))
            s, mean, sharpe = build_state(window, trades_by_now)
            if not math.isnan(sharpe):
                best_sharpe = max(best_sharpe, sharpe)
            passed, _ = factory.promotion_check(s, mean, sharpe, bench_map,
                                                 n_tests, R)
            if passed and not ever_passed:
                ever_passed, first_pass_day = True, end

        final_state, final_mean, final_sharpe = build_state(rows, n_trades)
        dd = final_state["equity"] / final_state["peak"] - 1
        results.append(dict(
            name=name, fn=params.get("fn"), sector=params.get("sector"),
            days=len(rows), trades=n_trades,
            total_return=final_state["equity"] - 1.0,
            sharpe=final_sharpe, best_sharpe=best_sharpe,
            drawdown=dd, ever_passed=ever_passed,
            first_pass_day=first_pass_day))

    ok = [r for r in results if "error" not in r]
    ok.sort(key=lambda r: (not r["ever_passed"], -(r["best_sharpe"]
                                                    if r["best_sharpe"] > -math.inf else -99)))

    print("=" * 100)
    print(f"{'strategy':<28}{'trades':>7}{'total ret':>11}"
          f"{'sharpe':>9}{'best':>8}{'maxDD':>9}{'ever cleared bar?':>20}")
    print("-" * 100)
    for r in ok:
        best = ("n/a" if r["best_sharpe"] <= -math.inf
                else f"{r['best_sharpe']:.2f}")
        verdict = (f"YES (day {r['first_pass_day']})" if r["ever_passed"]
                   else "no")
        print(f"{r['name']:<28}{r['trades']:>7}"
              f"{r['total_return']*100:>10.1f}%"
              f"{r['sharpe']:>9.2f}{best:>8}"
              f"{r['drawdown']*100:>8.1f}%{verdict:>20}")
    print("=" * 100)

    never = [r for r in ok if not r["ever_passed"]]
    zero_trade = [r for r in ok if r["trades"] == 0]
    print(f"\n{len(never)} of {len(ok)} strategies NEVER cleared the "
          f"promotion bar at any weekly checkpoint in "
          f"{advisors.TRAIN_PERIOD} of real history.")
    if zero_trade:
        print(f"{len(zero_trade)} never placed a single trade across the "
              f"whole period -- their trigger is unreachable at real "
              f"volatility, not merely unlucky so far:")
        for r in zero_trade:
            print(f"    {r['name']}")

    print("\n--- WHAT TO DO WITH THIS ---")
    print("KILL candidates (never traded in 5 years): the strongest case, "
          "since 'never triggered' is a property of the mechanism and the "
          "market, not of luck. Retiring these lowers the multiplicity "
          "bar for every surviving strategy.")
    print("WEAKER kill candidates (traded but never cleared the bar): real "
          "evidence against, but one historical period is one draw -- "
          "weigh alongside their live record.")
    print("NOTHING here promotes anything. A strategy that cleared the bar "
          "historically still has to earn it live; backtests flatter, and "
          "today's index membership is not the past's.")
    print("\nNo ledger was read for verdicts, written, or modified by this "
          "script. Retirement is a separate, explicitly authorized step.")


if __name__ == "__main__":
    main()
