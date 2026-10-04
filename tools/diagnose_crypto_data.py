"""
One-off diagnostic (CE-3-02): is yfinance usable as a daily crypto data source?

Question answered per ticker: how many daily rows, how far back, what share of
calendar days are present, are weekends covered (crypto trades 7 days/week, so
a feed that skips Sat/Sun is an equity-style feed and not usable for the
crypto profile), how many gaps > 1 day, and how many exactly-0.0 returns
(a phantom-day indicator: a forward-filled weekend shows up as a 0.0 return).

Also prints a 10-row tail of the close panel and, if Volume is returned, a
1-year average dollar-volume ranking for the universe rule (BTC, ETH + up to 8
more by 1y average volume; stablecoins excluded by a hard-coded list).

This sandbox cannot reach Yahoo Finance (documented env fact); this script is
meant to run on a GitHub Actions runner via
.github/workflows/diagnose_crypto_data.yml. Read-only: prints, writes nothing.
Fails loudly (exit 1) if the download returns nothing.

VERDICT per ticker:
  USABLE   >= 4 years of history AND calendar coverage >= 98% AND weekend coverage >= 95%
  GAPPY    calendar coverage 90-98% (and not USABLE)
  UNUSABLE everything else

USAGE: python tools/diagnose_crypto_data.py [--tickers BTC-USD ETH-USD ...] [--years 5]
"""
import argparse
import sys

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_TICKERS = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
                   "ADA-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "LTC-USD",
                   "DOT-USD", "TRX-USD"]
STABLECOINS = {"USDT", "USDC", "DAI", "BUSD", "TUSD", "FDUSD"}

MIN_YEARS = 4.0
USABLE_COVERAGE = 98.0
GAPPY_COVERAGE = 90.0
USABLE_WEEKEND = 95.0


def is_stablecoin(ticker):
    return ticker.split("-")[0].upper() in STABLECOINS


def download(tickers, years):
    """Return (close, volume) DataFrames; raise SystemExit if nothing came back."""
    try:
        raw = yf.download(tickers, period=f"{years}y", interval="1d",
                          auto_adjust=True, progress=False)
    except Exception as e:  # network/Yahoo failure must be loud, not silent
        print(f"FATAL: yfinance download raised {type(e).__name__}: {e}")
        sys.exit(1)
    if raw is None or len(raw) == 0 or "Close" not in raw:
        print("FATAL: yfinance download returned no data at all "
              f"(tickers={tickers}, years={years}). Cannot assess feasibility.")
        sys.exit(1)
    close = raw["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    close = close.dropna(how="all")
    if close.empty:
        print("FATAL: yfinance returned a Close panel with no non-NaN rows.")
        sys.exit(1)
    vol = raw["Volume"] if "Volume" in raw else None
    if isinstance(vol, pd.Series):
        vol = vol.to_frame(tickers[0])
    return close, vol


def analyse(series):
    """Stats dict for one ticker's close series (NaN already dropped)."""
    s = series.dropna()
    if len(s) < 2:
        return {"rows": len(s), "verdict": "UNUSABLE"}
    idx = pd.DatetimeIndex(s.index).normalize()
    first, last = idx[0], idx[-1]
    span_days = (last - first).days + 1
    cal_cov = 100.0 * len(idx.unique()) / span_days
    full = pd.date_range(first, last, freq="D")
    weekend_days = full[full.dayofweek >= 5]
    weekend_cov = (100.0 * weekend_days.isin(idx).sum() / len(weekend_days)
                   if len(weekend_days) else 0.0)
    diffs = pd.Series(idx[1:] - idx[:-1]).dt.days
    gaps = diffs[diffs > 1]
    longest_gap = int(gaps.max()) if len(gaps) else 1
    rets = s.pct_change().dropna()
    zero_ret = int((rets == 0.0).sum())
    years = span_days / 365.25
    if years >= MIN_YEARS and cal_cov >= USABLE_COVERAGE and weekend_cov >= USABLE_WEEKEND:
        verdict = "USABLE"
    elif GAPPY_COVERAGE <= cal_cov < USABLE_COVERAGE:
        verdict = "GAPPY"
    else:
        verdict = "UNUSABLE"
    return {"rows": len(s), "first": first.date(), "last": last.date(),
            "years": years, "cal_cov": cal_cov, "weekend_cov": weekend_cov,
            "n_gaps": int(len(gaps)), "longest_gap": longest_gap,
            "zero_ret": zero_ret, "verdict": verdict}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS)
    ap.add_argument("--years", type=int, default=5)
    args = ap.parse_args()
    tickers = list(args.tickers)

    close, vol = download(tickers, args.years)

    print(f"Downloaded {len(close)} rows x {close.shape[1]} columns "
          f"({args.years}y requested, daily, auto_adjust=True)\n")
    results = {}
    for t in tickers:
        if t not in close.columns or close[t].dropna().empty:
            print(f"[{t}] NO DATA returned -> VERDICT: UNUSABLE\n")
            results[t] = "UNUSABLE"
            continue
        r = analyse(close[t])
        results[t] = r["verdict"]
        if "first" not in r:
            print(f"[{t}] only {r['rows']} row(s) -> VERDICT: UNUSABLE\n")
            continue
        print(f"[{t}] rows={r['rows']}  first={r['first']}  last={r['last']}  "
              f"history={r['years']:.2f}y")
        print(f"    calendar-day coverage = {r['cal_cov']:.2f}%   "
              f"weekend coverage = {r['weekend_cov']:.2f}%")
        print(f"    gaps > 1 day = {r['n_gaps']}   longest gap = {r['longest_gap']} day(s)   "
              f"days with exactly 0.0 return = {r['zero_ret']} (phantom-day indicator)")
        print(f"    VERDICT: {r['verdict']}\n")

    print("=== VERDICT TABLE ===")
    for t in tickers:
        print(f"{t:<12} {results[t]}")

    print("\n=== Close panel, last 10 rows ===")
    print(close.tail(10).to_string())

    print()
    if vol is None or vol.empty:
        print("Volume not returned -- cannot rank by 1y average dollar volume.")
    else:
        rank = {}
        for t in tickers:
            if is_stablecoin(t) or t not in vol.columns or t not in close.columns:
                continue
            dv = vol[t].dropna().iloc[-365:]   # Yahoo crypto Volume is already USD; do NOT multiply by price (CE-3-03)
            if len(dv):
                rank[t] = float(dv.mean())
        if rank:
            ordered = sorted(rank.items(), key=lambda kv: -kv[1])
            print("1y average dollar volume ranking (stablecoins excluded: "
                  f"{sorted(STABLECOINS)}): "
                  + ", ".join(f"{t}={v/1e9:.2f}B" for t, v in ordered))
        else:
            print("Volume present but no rankable tickers (all excluded or empty).")


if __name__ == "__main__":
    main()
