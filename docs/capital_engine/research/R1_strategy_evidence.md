# R1 — What systematic trading evidence actually says (research record, 2026-10-03)

Collected by a low-cost research worker (Sonnet) on 2026-10-03 at Het's
instruction to ground the Capital Engine in "reality-based research, not what
most people are doing." METHOD NOTE from the worker: primary PDFs on SSRN, NSE,
Business Standard and Berkeley were blocked by the sandbox egress proxy, so every
figure comes from search-result summaries, not from reading the primary
documents. Items marked UNVERIFIED could not be sourced. Secondary-source numbers
are labelled. Facts only; the design conclusions drawn from them live in
`../00_DESIGN.md`.

## 1. Base rates (retail / day traders)

- **Chague, De-Losso, Giovannetti, "Day Trading for a Living?"** (Brazil index
  futures, 19,646 individuals starting 2013-15). Of those who persisted >300
  days, 97% lost money; 1.1% earned more than minimum wage; no evidence of
  learning. Net/gross of costs not stated in snippets (UNVERIFIED).
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101
- **Barber, Lee, Liu, Odean (Taiwan 1992-2006).** <1% of day traders in a given
  year are predictably profitable net of fees; average loss 23.9 bp/day net;
  >75% quit within 2 years.
  https://www.sciencedirect.com/science/article/abs/pii/S1386418113000190
- **Barber & Odean 2000** (66,465 US households 1991-96): most active traders
  earned 11.4%/yr vs market 17.9%. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=219228
- **Barber et al. 2009 (Taiwan 1995-99):** aggregate individual-investor
  penalty 3.8 pp/yr; of the loss, commissions and transaction taxes exceeded
  gross trading losses.
- **SEBI, Indian equity F&O individuals (after costs; secondary news sources):**
  FY22 89% lost; FY22-24 93% lost, aggregate loss > Rs 1.8 lakh crore, ~1 crore
  traders, avg loss ~Rs 2 lakh, >75% of loss-makers kept trading, 1% earned
  > Rs 1 lakh; FY25 ~91% lost, net loss Rs 1,05,603 crore (+41% YoY), avg loss
  ~Rs 1.1 lakh, ~9.6 million individuals; FY26 87.7% lost, net loss Rs 91,685
  crore, options = 92% of losses, active traders fell 98.1 lakh → 78.6 lakh.
  https://www.benzinga.com/24/09/40994647/sebi-study-unveils-93-of-individual-f-o-traders-suffered-losses-between-fy22-and-fy24
  https://www.thestatesman.com/business/nearly-91-pc-of-retail-investors-incur-net-loss-in-equity-derivatives-in-fy25-sebi-1503454878.html
  https://www.finnovate.in/learn/blog/sebi-fno-trader-losses-fy26-individual-derivatives
- **SEBI, intraday equity cash FY23:** >70% lost; 80% of those with >500
  trades/yr lost; loss-makers spent a further 57% of losses on costs.
  https://www.businesstoday.in/markets/story/seven-out-of-10-individual-intraday-traders-in-equity-cash-segment-make-losses-finds-sebi-study-438624-2024-07-24
- **Crypto retail (BIS Bulletin 69, Feb 2023, 95 countries):** 73-81% of retail
  investors likely lost on their initial investment. https://www.bis.org/publ/bisbull69.htm

## 2. Trend following / time-series momentum

- **Moskowitz-Ooi-Pedersen 2012 (JFE):** 58 futures/forwards 1985-2009;
  significant TSMOM in every instrument, persistence 1-12 months, partial
  reversal after; best in extreme markets. Sharpe/cost figures UNVERIFIED.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463
- **Hurst-Ooi-Pedersen, "A Century of Evidence" (1880-2013):** diversified
  Sharpe 0.77 gross; ~0.4 per market net of transaction costs; positive in every
  decade. https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing
- **Live indices, net of fees:** SG Trend ~5.2% CAGR since 2000, max DD 20.6%;
  SG CTA 4.8% ann. 2000-May 2024; SG Trend 2009-2018 only 0.4-1.8% ann. (max DD
  21.8%); BTOP50 ~flat 2009-2019 while equities ~+200% (single trade-press
  claim); 2022 +14.9%; 2025 +2.4%. No direct live-vs-backtest study found
  (UNVERIFIED). https://www.toptradersunplugged.com/trend-following-performance-report-december-2025/
  https://www.aima.org/article/trend-following-what-s-not-to-like.html

## 3. India: momentum, low-volatility, alpha indices (mostly BACKFILLED history)

- **Nifty200 Momentum 30:** launched 25 Aug 2020, earlier history backfilled.
  NSE whitepaper (Apr 2026): 19.19% CAGR vs 15.08% Nifty 200, Apr 2005-Feb
  2026 (backtest-dominated). Inception SD 22.6%. 2008 DD -67.9% vs -64.6% Nifty
  50; 2020 -34.2% vs -39.6%; recent ~-27% over 6 months vs Nifty 50 -12%
  (snippet, date UNVERIFIED).
  https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf
  https://freefincal.com/nifty200-momentum-30-index-a-new-strategy-index-from-the-nse/
- **Nifty100 Low Volatility 30:** base Apr 2005, launched Jul 2016; inception
  SD 16.83, beta 0.76 vs Nifty 50. Return table UNVERIFIED.
  https://www.niftyindices.com/Factsheet/Nifty100_LowVolatility30.pdf
- **Nifty Alpha 50:** lost >77% in 2008 (backfilled) vs ~-52% Nifty 50.
- **Academic:** Sehgal & Jain 2011 find 3-6 month momentum in India, largely
  sectoral. Net-of-cost magnitudes not retrieved.
  https://www.emerald.com/insight/content/doi/10.1108/09727981111129327/full/html
- **Post-publication decay (US, McLean & Pontiff JF 2016):** 97 predictors;
  returns 26% lower out-of-sample, 58% lower post-publication.
  https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365

## 4. Crypto

- **Liu & Tsyvinski 2021 (RFS):** strong time-series momentum and attention
  predictability 2011-18; magnitudes UNVERIFIED. https://www.nber.org/papers/w24877
- **Liu, Tsyvinski & Wu 2022 (JF):** market/size/momentum capture the
  cross-section. https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119
- **Zarattini, Pagani, Barbon (SFI RP 25-80, Apr 2025):** ensemble Donchian
  trend rules, top-20 liquid coins, survivorship-bias-free since 2015: Sharpe
  >1.5 and 10.8% annual alpha vs BTC NET of fees, significantly lower drawdowns
  than passive (exact DD UNVERIFIED). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5209907
- **Man Institute, "In Crypto We Trend":** liquidity ample for top ~15 coins,
  declines sharply after; beyond a point costs outweigh diversification.
  https://www.man.com/insights/in-crypto-we-trend
- **Drawdowns (secondary):** BTC -83/84% (2017-18), -77% (2021-22), ~-52/54%
  from the Oct 2025 peak (~$126k) to mid-2026 (~$58-60k); ETH -93/94% (2018),
  -81% (2022). BTC realised vol 57% (Feb 2021-Feb 2026).
- Retail fee/slippage effect on a simple BTC trend rule: no sourced number
  (UNVERIFIED).

## 5. Options for retail

- **Cboe PUT 1986-2018 (Bondarenko):** 9.54% vs 9.80% S&P, SD 9.95% vs 14.93%,
  Sharpe 0.65 vs 0.51, max DD -32.7%; index returns exclude retail bid-ask,
  margin, taxes. **BXM:** 11.77% vs 11.67%, SD 9.29% vs 13.89%, max DD ~-40%.
  https://cdn.cboe.com/resources/education/research_publications/PutWriteCBOE19_v14_by_Prof_Oleg_Bondarenko_as_of_June_14.pdf
- **Israelov & Nielsen 2015:** the short-vol component of a covered call has
  Sharpe ~1.0 but is <10% of its risk; equity exposure drives the rest. The
  volatility risk premium averaged 3.4% (1990-2014), positive 88% of the time;
  long options and puts are costly. https://papers.ssrn.com/sol3/Papers.cfm?abstract_id=2444999
- **Bondarenko:** ATM puts average -39%/month excess return, deep OTM -95%/month.
- **Retail option BUYING:** Bryzgalova-Pavlova-Sikorskaya (JF 2023): retail
  prefers cheap weeklies, quoted spreads up to 12.6%, loses on average.
  Beckmeyer-Branger-Gayda: US retail lost ~$241k/day (2021-23). **No evidence
  found that retail option buying is systematically profitable.** India: options
  = 92% of FY26 individual F&O losses.
  https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13285

## 6. Portfolio construction

- **Moreira & Muir 2017 (JF):** volatility-managed portfolios raise Sharpe for
  market/value/momentum/etc. in sample. **Cederburg et al. (JFE 2020), 103
  anomalies:** the benefit largely does NOT survive out of sample; managed
  portfolios don't systematically beat unmanaged. (Both sides recorded on
  purpose.) https://alphaarchitect.com/the-performance-of-volatility-managed-portfolios/
- **Asness-Frazzini-Pedersen (FAJ 2012):** leverage aversion → safer assets
  have higher risk-adjusted returns (risk-parity rationale).
- **2022 stress (secondary):** 60/40 ~-23%; risk parity -19.5% to -24.3%.
- **Rebalancing (Vanguard):** monthly vs annual: no meaningful risk-adjusted
  difference; threshold rebalancing ~15-25 bp/yr cost (from summary).
  https://corporate.vanguard.com/content/dam/corp/research/pdf/rational_rebalancing_analytical_approach_to_multiasset_portfolio_rebalancing.pdf

## 7. Statistical pitfalls

- **Harvey-Liu-Zhu (RFS 2016):** a new factor needs t > 3.0; most claimed
  findings likely false. https://academic.oup.com/rfs/article/29/1/5/1843824
- **Bailey & López de Prado, Deflated Sharpe (JPM 2014);** **Bailey et al. (AMS
  Notices 2014):** with 5 years of data, >45 independent configurations tried
  → the best in-sample strategy shows Sharpe ≥ 1.0 by chance.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2308659
- **MinTRL:** annualised Sharpe 2 needs 2.73 years to be shown > 1 at 95%.
  https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf
- **Worker's own i.i.d. calculation (not sourced), years to reject Sharpe 0:**

  | Threshold | Sharpe 0.5 | Sharpe 1.0 |
  |---|---|---|
  | one-sided 95% | ~10.8 y | ~2.7 y |
  | t = 2 | 16 y | 4 y |
  | t = 3 (HLZ) | 36 y | 9 y |

  This is the same arithmetic as `docs/research/Q5_statistical_power.md`
  and the reason the promotion bar now requires beating the benchmark with a
  multiplicity correction.
