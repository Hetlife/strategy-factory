# Capital Engine — design record (2026-10-03)

**Status: DESIGN ADOPTED on branch; nothing here is merged, enabled, or funded.**
Written by the high-reasoning session Het asked to "build it towards a finished
product … and create the handoff package so low-token models can finish the
work." Facts come from `research/R1_strategy_evidence.md` (what works) and
`research/R2_india_regulatory_venues.md` (India rules, tax, venues, data).
Mechanics live in `.autonomous/capital_engine/work_orders/`. This file is the
*why* and the *shape*; it does not repeat either of those.

`EXECUTION_PLAN.md` still wins on settled facts, gates, kill conditions and
guardrails. Where Het's 2026-10-03 directive reopens a settled decision (crypto,
F&O), §8 below says exactly what he has to write for the change to take effect.

---

## 0. The honest one-paragraph verdict

The base rates are brutal and they are *measured*: 87.7-93% of Indian
individual F&O traders lose after costs (SEBI, FY22-FY26), 73-81% of retail
crypto investors likely lost on their initial stake (BIS 2023), and <1% of day
traders are predictably profitable (Barber/Odean; Chague et al.). The only
approaches with documented, net-of-cost, out-of-sample evidence are *slow*:
diversified trend following (Sharpe ~0.4 per market net, century-long; live CTA
indices ~5% CAGR with ~21% drawdowns and a near-flat 2009-2019), slow crypto
trend on the top-liquid coins (Sharpe >1.5 net of fees, 2015-2025, one 2025
study), and fully-collateralised index put/call writing (PUT/BXM Sharpe ~0.65 vs
~0.5 for the index, with -33%/-40% drawdowns). Everything fast — day trading,
option buying, leverage — has the evidence stacked against it. So the engine
below is built to be slow, diversified, collateralised, tax-aware, and to earn
every rupee of real exposure through evidence. That IS the "software that
really works for making money": the version that survives long enough for an
edge, if one exists, to show up in the ledger. A version that promises more
would be the thing SEBI's numbers describe.

## 1. What Het asked for, and what this design does with it

| Het (2026-10-03) | Decision |
|---|---|
| Three asset classes under one factory | Yes — one engine, three *profiles* (§4). The existing NSE equity arena is the base and becomes sub-sleeve A2. |
| Low-risk class = 50%, safeguards the other two | Yes — class A is a **floor** of 50% of real capital and the only place real money goes on day one (§3). |
| Crypto / liquid volatile class | Yes as **paper** now (allowed under LucyOS contract C9: research, backtesting, paper trading). Reverses `EXECUTION_PLAN.md` §9's "Crypto → rejected"; needs the one-line amendment in §8. Tax regime makes only low-turnover hypotheses admissible (§7). |
| F&O class "based on the algorithm that studies both other classes" | **Designed, not built.** Hard rule (`CLAUDE.md`); declined twice before for a dedicated conversation. It is a *meta* layer so it is naturally last. Exact authorization text in §8; full design in `CE-X-01`. |
| Teams / sub-agents per class | Yes, cheaply: the existing `agents/` roles run per profile (§4). Worker count is not progress (LucyOS C6). |
| Harness + health check so bugs never restrict growth | Yes — golden-master regression, per-profile health harness, kill switch, gate evaluator (`CE-1-01`, `CE-1-04`, `CE-4-01`, `CE-4-02`). |
| Runs on LucyOS as the third project; SIP from the other two when profitable | Yes — `PROJECTS/strategy-factory/` definition + money path on a LucyOS branch (`CE-5-01`); SIP is an owner-only money-path step, never automated (`CE-X-03`). |
| "I can give it access to platforms with real money … build it so it can get there" | The *path* is built (contract `CE-4-03`, gates `CE-4-01`, broker order `CE-X-02`). Real-money code is not written until §8's sentences exist. Law 3 and C9 are not loosened by this document. |
| Lump sum invested from the start, divided and risk-regulated | On day one a funded engine holds 100% in A1 (liquid/G-sec/gold/Nifty ETF core). B and C hold Rs 0 real until they earn rung 1 (§3). That is the risk regulation. |

## 2. The three classes

| Class | Name | Ceiling of real capital | Sub-sleeves | Benchmark it must beat | Status today |
|---|---|---|---|---|---|
| **A** | SHIELD | **50% floor**, up to 100% | A1 passive core (liquid ETF, G-sec/target-maturity ETF, gold ETF, Nifty 50 ETF; fixed weights + bands) · A2 the existing NSE equity arena (`factory.py`, capital earned via `LADDER`) | A1: the liquid ETF · A2: `nifty_benchmark` (live) | A2 live paper since 2026-07-13; A1 hypothesis to write (`CE-2-01`) |
| **B** | VELOCITY | ≤ 30% | B1 slow trend long-or-flat on BTC, ETH + ≤8 liquid coins · B0 cash baseline | BTC buy-and-hold AND cash, post-tax | Hypothesis to write (`CE-3-01`), data feasibility (`CE-3-02`) |
| **C** | DERIVATIVES | ≤ 20% | Fully-collateralised Nifty index option writing (only side with evidence); reads A and B regime state | Nifty 50 buy-and-hold AND class A core, post-tax | GATED (`CE-X-01`) |

Ceilings are *maximums*, not targets. "SGB" is read as gold ETF because new SGB
tranches stopped in Feb 2024 (R2 §3). "Companies" = A2.

## 3. Capital, risk budget and what actually happens on day one

1. **Only earned exposure is real exposure.** Each class has its own ladder;
   a contestant reaches rung 1 only through `promotion_check()` (beat benchmark
   on date-paired excess returns + multiplicity-corrected Sharpe floor). Nothing
   in this design grants capital to B or C. Day-one real allocation of a funded
   engine: 100% A1. This is Law 3, applied at the portfolio level.
2. **Class ceilings bind at promotion time**: a promotion that would push a
   class over its ceiling is recorded as PROMOTE-BLOCKED-BY-CEILING and the
   contestant keeps paper status (new verdict string, no RULES change).
3. **Portfolio drawdown rules (pre-committed, evaluated by `portfolio/`):**
   -10% from the portfolio's real-money peak → B and C to paper for 90 days;
   -15% → everything to A1's liquid ETF and the `KILL` file is written.
   Why these numbers: a plain 60/40 lost ~23% and risk parity ~19-24% in 2022
   (R1 §6), so "defensive" is not "cannot fall"; 10%/15% are the levels at which
   the A floor still covers the loss with the sleeve weights above.
4. **Volatility cap, not volatility targeting.** Per-coin and per-sleeve
   exposure is capped at 2× BTC's trailing vol / the A1 target vol; we do NOT
   lever up in calm markets, because Cederburg et al. (R1 §6) show vol-managed
   gains largely vanish out of sample.
5. **No leverage, no shorting, no margin beyond collateral held**, in any class,
   ever, by construction in the signal functions (hard rule).
6. **Rebalance cadence:** weekly for all classes (R1 §6: more frequent adds
   cost without risk-adjusted benefit; India's 1% crypto TDS makes every extra
   sale a direct cash drag).

## 4. One engine, three profiles, one team

- `factory.py` stays the only trading engine. `CE-1-02` adds a JSON *profile*
  (universe, benchmark, calendar, cost parameters, tax model, state dir) chosen
  by `FACTORY_PROFILE`, defaulting to today's `equity_nse` with a golden-master
  test proving byte-identical behaviour. Each class = one profile = its own
  ledger under `factory_state/<profile>/`. `RULES`/`LADDER`/`COST_PER_SIDE` for
  equity stay literal in code and protected; other profiles may *propose* rules
  that stay inert until Het enables the profile.
- Workflows matrix over enabled profiles (`CE-1-03`); supervisor and health
  harness run per profile (`CE-1-04`); the aggregator (`CE-2-03`) is the only
  portfolio-level view and it is read-only.
- **Teams:** `agents/` (judge, researcher, breeder, risk_manager, reporter,
  healer, master_trader, hr) are already read-only/advisory and parameterised by
  the ledger they read, so one `--profile` flag gives every class its own
  "team" at zero new code. New roles only through `agents/hr` when a real gap is
  observed. Nothing in `agents/` ever gains a write path to a ledger.
- **LucyOS owns orchestration, approvals, secrets, the money path and the
  phone view; this repo owns strategies, evidence and the engine.** No second
  scheduler, queue, approval system or secret store is built in either place
  (LucyOS D-1, anti-dup guard; this repo's `P0-5` history).

## 5. Data and venue decisions (free first)

| Need | Decision | Why / fallback |
|---|---|---|
| NSE prices | yfinance on GitHub Actions (as today) | Free, already validated. Fallback: NSE UDiFF bhavcopy (free, official, R2 §6) via `jugaad-data` — becomes the duplicate/phantom-day oracle too (NSE 2026 holiday list in R2). |
| Crypto prices | yfinance `BTC-USD`-style tickers, **tested on Actions first** (`CE-3-02`) | Fallback: Binance public REST/WebSocket (no key) or CoinGecko demo tier. |
| F&O data | NSE F&O bhavcopy (EOD, free) | Only if `CE-X-01` is authorised; intraday chains are not free. |
| NSE broker (when authorised) | Shortlist **Dhan** or **Upstox**: free trading API + sandbox (R2 §4). Zerodha personal API is free but has no sandbox and no data. | Decision recorded at authorization time, not now. SEBI retail-algo framework: ≤10 orders/sec needs no registration; static IP + Algo-ID tagging required from 2026-04-01. |
| Crypto venue (when authorised) | FIU-registered exchange with a documented API — **CoinDCX** candidate (R2 §5) | Binance India is P2P-funded only. |
| Secrets | LucyOS scoped store, names only (`PJ_strategy-factory__…`) | Never in this repo; `aion scan` gate. |

## 6. Gates to real capital (codified in `CE-4-01`)

G1 evidence (rung-1 promotion through the real gate) · G2 independent validation
in a different session (LucyOS C9) · G3 portfolio limits · G4 a fresh, dated,
specific `AUTHORIZE REAL CAPITAL <class> <contestant> <amount>` line from Het ·
G5 infrastructure (kill switch live, reconciliation designed). RED anywhere =
no real money. Today: RED on every class (G1 unmet; zero promotions ever).

**Kill conditions (added to `EXECUTION_PLAN.md` §5's list, same force):**
(g) class B after 12 paper months: best contestant's post-tax excess over BTC
buy-and-hold ≤ 0 or max DD > 40% → B stays paper indefinitely; (h) portfolio
rules in §3.3; (i) a reconciliation mismatch between broker and ledger → KILL.

## 7. Economics, stated without optimism

- **Tax is the largest cost in two of three classes.** Crypto: 30% flat on gains,
  *no loss set-off*, 1% TDS on every sale. A strategy that wins 55% of trades at
  1:1 is profitable pre-tax and *loses* post-tax under no-offset. Hence only slow,
  low-turnover, long-or-flat hypotheses are admissible for B, and the class's
  own `post_tax_expectancy` models the no-offset rule per financial year.
  F&O: STT rose 2026-04-01 (futures 0.05%, option premium 0.15%); income is
  business income at slab rates with audit thresholds.
- **A1's realistic return is repo (5.25%) to 10-yr G-sec (7.13%) plus a small
  rebalancing bonus, minus 0.2-0.8% ETF expense.** That is its job. It is not
  where returns come from; it is why the engine is still alive in year three.
- **Expected outcome, honestly:** the most likely result of 12-24 months of paper
  across A2 and B is that one or zero contestants clear the bar. GOALS.md says
  that is a legitimate success ("buy the index"). Nothing here changes that.
- **Growth lever ranking is unchanged** (`EXECUTION_PLAN.md` §9): contribution
  rate > survival > edge. The SIP step (`CE-X-03`) is lever #1 and is owner-only.

## 8. Authorizations Het must give — exact sentences, in session, each separately

Nothing below carries forward from this message or any earlier "every
permission" grant. A session copies the sentence into `.autonomous/het_directives.md`
with the date when he writes it.

| # | Unlocks | Sentence Het writes |
|---|---|---|
| A1 | `CE-0-01` merge of this package to `main` | `merge CE-0-01` |
| A2 | Crypto as a **paper** class; amends `EXECUTION_PLAN.md` §9 "Crypto → rejected" to "Crypto → paper research class B, no real capital" | `AUTHORIZE CLASS B PAPER` |
| A3 | Enabling a non-equity profile's proposed `rules`/`ladder` (financial parameters) | `ENABLE PROFILE <shield_nse|crypto> WITH RULES AS PROPOSED` (after reading the proposal in the profile JSON) |
| A4 | Adding **paper-only** futures/options simulation logic (hard rule `CLAUDE.md`: options/futures/leverage) | `AUTHORIZE CLASS C PAPER — I have read CE-X-01 and R1 §5 and accept that this adds derivatives logic to the codebase` |
| A5 | Any broker/exchange adapter code, read-only first (hard rule: broker/execution/API-key code) | `AUTHORIZE BROKER ADAPTER READ-ONLY <broker>` |
| A6 | Real capital for one contestant in one class, after CE-4-01 shows AMBER | `AUTHORIZE REAL CAPITAL <class> <contestant> <amount>` |

Until A2 is written, `CE-3-*` orders may still produce the *hypothesis
documents* (free, no code) but no `crypto` profile is created. Until A4, no
derivatives code exists in the repository, and `CE-X-01` stays a document.

## 9. Critical path (strict order; details in the work orders)

```
CE-0-01 merge → CE-0-02 run acceleration tools → CE-0-03 retire packet (Het)
CE-1-01 golden master → CE-1-02 profiles → CE-1-03 matrix → CE-1-04 harness
CE-2-01 A hypothesis → CE-2-02 shield profile → CE-2-03 aggregator
CE-3-01 B hypothesis → CE-3-02 data check → CE-3-03 crypto profile   (needs A2)
CE-4-01 gates → CE-4-02 kill switch → CE-4-03 adapter contract
CE-5-01 LucyOS definition (done) → CE-5-02 evidence sync
CE-X-01 F&O (A4) · CE-X-02 broker (A5) · CE-X-03 SIP (owner)
```
Executors are named per order (LucyOS lanes: DET > LOCAL_MODEL > CLAUDE_CODE >
FABLE). A Fable/high-reasoning session is needed again only for the reviews
marked "Fable review: YES" and for §8 conversations — not to re-plan.

## 10. Deliberately NOT built

- A persistent multi-agent orchestrator runtime (failed 5× here, `P0-5`; LucyOS
  D-1 forbids a second control plane).
- Automatic transfers/SIP, any bank/UPI integration (LucyOS C8, `risk.real-money`).
- Option *buying*, leverage, shorting, intraday anything (R1 §1, §5: no evidence).
- Volatility *targeting* that levers up (R1 §6 out-of-sample failure).
- A separate crypto or F&O engine (duplication; one engine, profiles).
- Any change to `RULES`, `LADDER`, `COST_PER_SIDE`, or any registry entry.
