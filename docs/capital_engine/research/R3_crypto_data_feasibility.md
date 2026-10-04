# R3 — Crypto data feasibility (yfinance, daily, 7 days/week)

**Status: STUB — no data result yet.** The sandbox cannot reach Yahoo Finance, so nothing below is a measurement. Do not read any verdict into this file until the real run output is pasted.

## What exists
- `tools/diagnose_crypto_data.py` — downloads daily closes (`auto_adjust=True`) for a crypto ticker list and prints, per ticker: rows, first/last date, % of calendar days present, weekend coverage %, gaps > 1 day, longest gap, count of exactly-0.0 returns (phantom-day indicator), and a VERDICT. Also prints a 10-row tail of the close panel and a 1-year average dollar-volume ranking (stablecoins excluded) when Volume is available. Exits non-zero with a clear message if the download returns nothing.
- `.github/workflows/diagnose_crypto_data.yml` — `workflow_dispatch` only, inputs `tickers` and `years`.

## Verdict rule
- USABLE: >= 4 years of history AND calendar coverage >= 98% AND weekend coverage >= 95%
- GAPPY: calendar coverage 90–98%
- UNUSABLE: otherwise

## How to dispatch
The workflow must be on `main` first (depends on CE-0-01). Then: GitHub -> Actions -> "Strategy Factory - Diagnose Crypto Data" -> Run workflow (defaults are the 12-ticker list, 5 years), or `gh workflow run diagnose_crypto_data.yml`.

## To fill in after the real run
- Run URL: _(paste)_
- Verdict table (paste from the Actions log): _(paste)_
- Dollar-volume ranking line: _(paste)_

## Fallback (candidate only, not built)
If yfinance proves unusable: Binance public REST klines (no API key).
