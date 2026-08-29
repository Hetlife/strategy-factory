"""
One-off diagnostic: does every ticker in UNIVERSE["nifty100"] actually
resolve on Yahoo Finance?

Origin: 2026-08-29, Het asked to add a Nifty 100 momentum contestant
(mom_nifty100_lb90, mechanism-first). The ~95-name basket was built from
training knowledge, not a live fetch -- this sandbox's egress proxy
blocks nseindia.com, en.wikipedia.org and smallcase.com (confirmed via
real attempted WebFetch calls), the same restriction class as the
documented Yahoo Finance block. A wrong/delisted ticker doesn't crash
the pipeline (fetch_prices just drops it from the panel), but it's a
real data-quality risk worth checking for real rather than leaving as a
flagged assumption for Het to eyeball by hand.

This sandbox can't reach Yahoo Finance (documented env fact) -- this
script is meant to run on a GitHub Actions runner, which can. Read-only,
prints findings, writes/commits nothing, never touches seed_registry()
or UNIVERSE itself.

USAGE: python tools/diagnose_nifty100_tickers.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import factory


def main():
    import yfinance as yf

    tickers = factory.UNIVERSE["nifty100"]
    print(f"Checking {len(tickers)} tickers in UNIVERSE['nifty100']...\n")

    px = yf.download(tickers, period="1mo", auto_adjust=True,
                      progress=False)["Close"]

    missing = []
    thin = []
    ok = []
    for t in tickers:
        if t not in px.columns:
            missing.append(t)
            continue
        n = px[t].notna().sum()
        if n == 0:
            missing.append(t)
        elif n < 15:   # ~1mo of trading days is ~21; <15 real prints is suspicious
            thin.append((t, n))
        else:
            ok.append(t)

    print(f"OK (real recent data): {len(ok)}/{len(tickers)}")
    if thin:
        print(f"\nTHIN DATA ({len(thin)}) -- resolved but suspiciously few real prints in the last month:")
        for t, n in thin:
            print(f"  {t}: {n} non-NaN closes")
    if missing:
        print(f"\nNO DATA / DID NOT RESOLVE ({len(missing)}):")
        for t in missing:
            print(f"  {t}")
    else:
        print("\nAll tickers resolved with data. No missing symbols.")

    if not thin and not missing:
        print("\nRESULT: clean. The full ~95-name basket is usable as-is.")
    else:
        print(f"\nRESULT: {len(missing)} missing + {len(thin)} thin out of "
              f"{len(tickers)} -- review before treating this as a settled basket.")


if __name__ == "__main__":
    main()
