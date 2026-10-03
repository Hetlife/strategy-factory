# CE-X-01 — Class C (NSE futures & options) — GATED, design-complete, build NOT authorised

**Status:** BLOCKED on an explicit, separate, in-session authorization from Het that names this work order. Twice before (2026-08-29, and the "master trader" ask 2026-08-27) F&O/leverage was declined and logged for a dedicated conversation; Het's 2026-10-03 directive re-opens it. The hard rule in `CLAUDE.md` ("Never add options/futures/margin/leverage logic") still stands until he writes the sentence in `00_DESIGN.md` §8 — this file exists so that when he does, nothing has to be re-thought.

**Why it is last in the critical path, not first:** Het's own description — "based on the algorithm which studies both of the other asset classes" — makes C a META layer: it needs A and B producing honest paper evidence before it has anything to study. And the base rate is the worst of the three (R1 §1: 87.7-93% of Indian individual F&O traders lose; options = 92% of losses).

## What the design would be (paper only, when authorised)
- Admissible hypotheses ONLY on the side with documented evidence: systematic short volatility with full collateral (cash-secured index put writing / covered calls; R1 §5: PUT/BXM Sharpe 0.65 vs 0.51 with -33%/-40% max DD, index-level, before retail spreads). Long-option buying has no supporting evidence anywhere in R1 and is excluded by hypothesis, not by data.
- Hard constraints encoded in the signal: margin never exceeds cash held in class C (no leverage beyond collateral), one index underlying (Nifty 50) only, monthly expiries only (SEBI's weekly-expiry rules in R2), max notional = class C ceiling.
- Data: NSE F&O bhavcopy (free, R2 §6); option-chain history is the hardest part — feasibility order first (mirror CE-3-02).
- Costs/tax: STT on options premium/exercise, exchange charges, SEBI fee, GST, stamp; business-income taxation with audit thresholds (R2 §3).
- Benchmark: Nifty 50 buy-and-hold AND class A's shield core — C must beat both post-tax or it is falsified.
- Kill: any day's mark-to-market loss > 5% of class C paper capital → the class goes flat for 30 days (pre-committed).

## Authorization needed (exact text Het must write, in session)
See `docs/capital_engine/00_DESIGN.md` §8, item F&O. Without it this order does not start.
