# A1 — Class A "shield core": diversified low-volatility carry (written 2026-10-04, before any data was touched)

Law 1: mechanism, instruments, rules, expectations and kill conditions are fixed
here BEFORE any backtest. Changes after seeing data require a new dated file
(a new registry key), never an edit to this one.

## 1. Mechanism (no numbers from data)
Four sleeves whose returns come from different sources — overnight money-market
yield (cash), sovereign duration (G-sec), an INR/crisis hedge priced in a
different currency and demand base (gold), and broad equity beta (Nifty 50) —
earn mostly *yield and risk premia*, not forecasts. Holding them at fixed
weights with wide rebalancing bands adds a small "rebalancing bonus" (sell what
rose, buy what fell) while keeping turnover, and therefore cost and tax, near
zero. The sleeve's job is capital preservation that funds the risk budget of
classes B and C (00_DESIGN.md §3), not outperformance.

## 2. Instruments (NSE-listed ETFs only, so the existing cost model applies)
| Sleeve | Candidate ticker (yfinance) | Expense (R2 §7) | Status |
|---|---|---|---|
| Cash / overnight | `LIQUIDCASE.NS` (Zerodha Nifty 1D Rate Liquid ETF, **growth NAV**, no daily payout) | UNKNOWN | verify on Actions. Chosen over `LIQUIDBEES.NS` because daily-dividend liquid ETFs keep a flat ~Rs 1,000 price, so a *price* series shows zero return and misstates the sleeve; a growth-NAV fund records the yield in price. Fallback: ICICI Pru BSE Liquid Rate ETF (TER 0.21%) if it is growth-style. |
| Sovereign duration | `LTGILTBEES.NS` (Nippon 8-13 yr G-sec Long Term Gilt BeES) | UNKNOWN | verify ticker, TER and liquidity on Actions; alternative: a Bharat Bond / target-maturity ETF with ≥ 3 yr to maturity |
| Gold | `GOLDBEES.NS` (Nippon Gold BeES; most liquid) | 0.69-0.81% (sources conflict) | alternative `HDFCGOLD.NS` at 0.59% if its spread is comparable |
| Equity beta | `NIFTYBEES.NS` (Nippon Nifty 50 BeES) | ~0.04% | — |
Tickers are candidates until `CE-2-02`'s data check (mirror of `CE-3-02`)
confirms ≥ 3 years of daily history and no >1-day gaps; a sleeve whose ETF
fails the check uses its named alternative, decided by a dated commit.

## 3. Rules (stated in advance)
- Target weights: **40% cash, 20% G-sec, 20% gold, 20% Nifty 50.** Rationale:
  half the sleeve in the near-riskless asset keeps the sleeve's own drawdown
  small; the three risk sleeves are equal-weighted because we claim no view on
  their relative returns (equal weight is the no-forecast prior).
- Band rebalancing: trade only when a sleeve's weight drifts more than **±5 pp
  absolute** from target, checked weekly in `report()`, at most one rebalance
  per week, back to target. Vanguard's evidence (R1 §6): more frequent
  rebalancing adds cost without risk-adjusted benefit.
- Signal function `sig_fixed_weight(px, p)` returns the target weights when a
  band is breached, otherwise the current drifted weights (no trade). Never
  short, never leveraged, gross exposure = 1.0.
- Costs: the existing size-aware equity model (`round_trip_cost`) — these are
  cash-segment ETF trades. Tax: gold and G-sec ETF gains at slab ≤ 12 months
  and 12.5% beyond (no Rs 1.25 lakh exemption); Nifty ETF as equity (R2 §3).
  Low turnover is what makes the sleeve's post-tax return ≈ pre-tax.

## 4. Benchmark
The cash sleeve's own ETF (`LIQUIDCASE.NS` or the chosen fallback) as a
permanent contestant `shield_cash_benchmark`: "doing nothing" in a liquid fund
is the bar. (The equity arena's `nifty_benchmark` is NOT this class's bar.)

## 5. Pre-committed expectations
Return ≈ repo rate (5.25%) to 10-yr G-sec (7.13%) + 0-1% rebalancing bonus −
0.2-0.8% expense ≈ **5-7%/yr nominal**; expected max drawdown **< 8%** in a
normal year. It will underperform Nifty in bull markets by design.

## 6. Falsification (pre-committed)
If realised max drawdown exceeds **12%**, or the sleeve trails the cash
benchmark over any rolling **24 months**, the hypothesis is FALSIFIED: the
profile goes to 100% cash ETF (a dated commit), and this file is marked
FALSIFIED with the numbers.

## 7. What would make us wrong
A simultaneous equity–duration–gold drawdown (2022-style: 60/40 −23%, risk
parity −19 to −24%, R1 §6); an INR shock that moves gold and equities
together; a liquid ETF whose growth NAV or liquidity assumption is wrong.

## 8. Owner sign-off
Het writes: "approved for paper trading as class A profile shield_nse". Until
then `CE-2-02` does not create the profile.
