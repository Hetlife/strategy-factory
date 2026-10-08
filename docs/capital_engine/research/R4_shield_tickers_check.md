# R4 — Class A shield tickers checked on a real runner (2026-10-08)

Run: https://github.com/Hetlife/strategy-factory/actions/runs/37731352258 (`diagnose_crypto_data.yml` reused with NSE tickers, 5y daily, yfinance 1.7.0). **The tool's USABLE/UNUSABLE verdicts are crypto-calibrated (they demand weekend bars) and read UNUSABLE for every NSE ticker; ignore them. The raw numbers below are the result.**

| Ticker (A1 §2 role) | Rows / first date | Zero-return days | Verdict for the shield |
|---|---|---|---|
| `LIQUIDCASE.NS` (cash, growth NAV) | 676 / **2024-01-17 (2.73y)** | 60 of 676 (9%) | **Confirmed as the cash sleeve.** Price rises steadily (116.10 on 09-25 to 116.27 on 10-08, about +0.15% in 13 days, roughly 4% a year annualised). The zero days are 2-decimal price rounding of a tiny daily accrual, not missing data. Limit: only 2.7 years of history, so a 5-year backtest of the full sleeve needs a proxy before 2024. |
| `LIQUIDBEES.NS` (rejected alternative) | 1239 / 2021-10-08 | **626 of 1239 (51%)** | **Rejected, as A1 predicted.** Price is pinned at about 1000 (payout-style fund), so a price series shows no return. Do not use it as the cash sleeve. |
| `LTGILTBEES.NS` (G-sec) | 1214 / 2021-10-08 | 110 (9%) | Usable for paper. Thin: under 5 million shares a day at about Rs 29.5 (under about Rs 15 crore a day), irrelevant at Rs 25,000 positions but a real constraint at scale. NaN on some days. |
| `GOLDBEES.NS` (gold) | 1239 / 2021-10-08 | 24 (2%) | **Confirmed.** Most liquid of the set. |
| `HDFCGOLD.NS` (named alternative) | 806 / 2023-06-08 (3.34y) | 9 | Not needed; shorter history than GoldBeES. |
| `NIFTYBEES.NS` (equity beta) | 1239 / 2021-10-08 | 10 | **Confirmed.** |

## Data-quality finding (affects every Yahoo-based profile)
In the same panel, 10-07 is missing (NaN) for GOLDBEES, NIFTYBEES and LIQUIDCASE even about 10 hours after the next morning began, while HDFCGOLD and LTGILTBEES have it; 10-02 (an NSE holiday) is forward-filled for some tickers and NaN for others. Yahoo's daily series for NSE has holes that do not necessarily fill later. The engine forward-fills them, and the phantom-day guard skips a row where at least 80% of tickers are unchanged, so no fake day is recorded. But a session Yahoo never fills is folded into the next day's return (a two-day return in one row) and the promotion clock counts one day fewer. This is harmless for paper research and must not be used for execution timing.

**Recommendation (a future order, not built):** reconcile or replace Yahoo with NSE UDiFF bhavcopy (free, official, about 30 to 60 minutes after close; R2 section 6) for the equity arena and the shield sleeve before any real-money step.

## Effect on the shield order
A1's four tickers stand as written (LIQUIDCASE, LTGILTBEES, GOLDBEES, NIFTYBEES). No change to the hypothesis document. Before the profile is ever enabled, `CE-2-02` needs no code change; the cash-history limit only matters for a historical backtest, which A1 does not require.
