# B1 — Class B: slow trend, long-or-flat, top-liquid coins (written 2026-10-04, before any crypto data was touched)

Law 1: this document fixes the mechanism, the universe rule, the parameter
*ranges* and the kill conditions BEFORE `CE-3-02` downloads a single bar.
Nothing below may be adjusted after looking at data except through a new,
dated hypothesis file (a new registry key), never by editing this one.

## 1. Mechanism (why a trend should exist and persist)
Crypto has no circuit breakers, trades 24/7, and its marginal buyer is a
slow-moving mix of retail flows, treasury allocations and ETF creations that
arrive over weeks, not minutes. Information and capital diffuse slowly, so
multi-week price trends form and persist (R1 §4: Liu & Tsyvinski 2021 find
strong time-series momentum; Zarattini et al. 2025 find ensemble Donchian
trend rules on the top-20 liquid coins earn Sharpe > 1.5 and ~10.8% annual
alpha vs BTC *net of fees*, 2015-2025, with lower drawdowns than passive).
Drawdown control comes from being FLAT in downtrends, not from forecasting.
Why slow: India taxes every realised crypto gain at 30% with NO loss set-off
and 1% TDS on every sale (R2 §3), so turnover is a direct, un-netted cost.

## 2. Universe rule (fixed before data)
BTC, ETH, plus up to 8 more coins ranked by 1-year average USD volume on the
date `CE-3-02` runs, excluding stablecoins, wrapped/pegged tokens and anything
launched < 2 years earlier (survivorship guard). The list is frozen in the
profile JSON with the ranking date; reviewed quarterly by a dated commit; a
coin leaving the list is closed to flat at the next weekly rebalance, never
mid-week. No mid-quarter additions. Only coins `CE-3-02` marks USABLE enter.
Fewer than 4 usable coins → the class runs with BTC and ETH only.

## 3. Rules (parameter ranges bounded by the mechanism, not fitted)
- Signal per coin, evaluated on daily closes: **long** if close > the
  trailing N-day Donchian channel midpoint, or close > the N-day simple
  moving average, per the rule type; otherwise **flat**. N ∈ {50, 100, 200}
  days only — shorter than 50 is noise relative to 1% TDS per sale; longer
  than 200 misses the roughly one-year cycles crypto has shown.
- Rule types: `donchian`, `sma`. Registry = 3 lookbacks × 2 types = **6
  contestants**, named `crypto_trend_<type>_<N>`. The multiplicity correction
  uses n = 6.
- Position: equal weight across coins currently long; gross exposure ≤ 1.0;
  **never short, never leveraged, never margin** (hard rule, enforced in code).
- Volatility cap: a coin whose trailing 90-day realised vol exceeds 2× BTC's
  gets half weight. No volatility *targeting* that scales exposure up (R1 §6).
- Rebalance: once a week, same weekday, using that day's close. Signals are
  computed daily for the record but acted on weekly.
- Costs modelled: 0.30% round-trip exchange fee + 0.10% spread (midpoint of
  R2 §5's 0.1-0.5% range; revisit only with a dated venue decision), 1% TDS
  on every sale as a cash drag, 30% tax on realised gains with no loss offset,
  computed per Indian financial year in `post_tax_expectancy_vda()`.

## 4. Benchmarks
`crypto_btc_benchmark`: always 100% BTC (buy-and-hold, the "just hold" bar),
permanent. `crypto_cash_baseline`: B0. Promotion requires beating BOTH on the
existing gate (date-paired excess returns + multiplicity-corrected Sharpe
floor), evaluated post-tax for this class.

## 5. Pre-committed expectations
Over a full cycle the strategy should keep most of BTC's upside with a max
drawdown materially below BTC's (BTC: -77% to -84% in 2018 and 2022, R1 §4);
trend following's own drawdowns are ~20-25% (R1 §2) and crypto's will be
larger. Long flat stretches in which the cash baseline wins are expected —
that is the design, not a failure. Expected trades: roughly 2-6 round trips
per coin per year.

## 6. Falsification (kill conditions, pre-committed)
After 12 months of paper: if the best contestant's post-tax excess return over
`crypto_btc_benchmark` is ≤ 0, OR its max drawdown exceeds 40%, OR it trails
`crypto_cash_baseline` post-tax, class B is FALSIFIED → stays paper
indefinitely, no profile rules enabled, no real capital, and this file is
marked FALSIFIED with the numbers. A single contestant promoting to rung 1 does
NOT by itself unlock real capital (gates G2-G5, `CE-4-01`).

## 7. What would make us wrong
A regime in which crypto trades like a high-beta equity index with fast
reversals (2022-23 style chop), making 50-200 day rules whipsaw; a venue or tax
change that raises per-sale cost further; data gaps that fake trends (hence
`CE-3-02` and the per-profile phantom-day check come first).

## 8. Owner sign-off
Het, 2026-10-04: "Authorize class b but make it effective and token friendly"
— recorded as §8 A2 (paper only). He may veto or amend this document before
`CE-3-03` builds it; silence is not consent for anything beyond paper.
