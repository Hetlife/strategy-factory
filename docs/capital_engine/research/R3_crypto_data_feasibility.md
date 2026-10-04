# R3 — Crypto data feasibility (REAL run on GitHub Actions, 2026-10-04)

Run: https://github.com/Hetlife/strategy-factory/actions/runs/37177876954 (`diagnose_crypto_data.yml`,
main at 7fd5ca3, yfinance 1.7.0, 5y daily, auto_adjust). Tool: `tools/diagnose_crypto_data.py`.

## Verdict table (verbatim)
```
Downloaded 1826 rows x 12 columns (5y requested, daily, auto_adjust=True)
every ticker: rows=1826  first=2021-10-04  last=2026-10-04  history=5.00y
              calendar-day coverage = 99.95%   weekend coverage = 99.81%
              gaps > 1 day = 1   longest gap = 2 day(s)   days with exactly 0.0 return = 0 (TRX-USD: 1)
BTC-USD USABLE · ETH-USD USABLE · BNB-USD USABLE · SOL-USD USABLE · XRP-USD USABLE · ADA-USD USABLE
DOGE-USD USABLE · AVAX-USD USABLE · LINK-USD USABLE · LTC-USD USABLE · DOT-USD USABLE · TRX-USD USABLE
1y average dollar volume ranking (stablecoins excluded): BTC > ETH > BNB > SOL > LTC > LINK > XRP > AVAX > DOT > ADA > TRX > DOGE
```
Conclusion: **yfinance crypto bars are USABLE as the class B data source** on GitHub
Actions: true 7-day calendar (weekend coverage 99.8%), one 2-day gap in 5 years,
no forward-filled phantom days (TRX has one exact-0.0 day). Binance public REST
stays the documented fallback (R2 §5), not built.

## Frozen class B universe (B1 §2 rule applied on 2026-10-04)
BTC + ETH + the next 8 by 1-year average dollar volume, stablecoins excluded,
all with ≥ 2 years of history (all have 5): **BTC, ETH, BNB, SOL, LTC, LINK, XRP,
AVAX, DOT, ADA.** Excluded by rank: TRX, DOGE. Wrapped/pegged tokens: none in
the candidate list. Review date: 2027-01-04 (quarterly), by a dated commit only.
Note on the ranking line: the printed dollar-volume *magnitudes* are implausible
(BTC "3488314.82B") — the tool multiplies a volume that Yahoo already reports in
USD by price. The ORDER is still correct for ranking purposes; the magnitude
bug is cosmetic and logged for CE-3-03 to fix in passing (tool-only, no
financial effect).

## Caveats
- Yahoo's crypto close is a UTC-midnight composite, not an Indian exchange price;
  INR conversion and exchange-specific spreads are modelled as costs (B1 §3).
- Data is adjusted/composite; the live run on Actions is the validation, not the
  sandbox (which cannot reach Yahoo).
