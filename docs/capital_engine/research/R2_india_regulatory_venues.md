# R2 — India: regulation, tax, venues, data, instrument costs (research record, 2026-10-03)

Collected by a low-cost research worker (Sonnet) on 2026-10-03. METHOD NOTE from
the worker: WebFetch was egress-blocked for every primary domain (sebi.gov.in,
nseindia, incometax.gov.in, broker sites); every fact comes from search-result
summaries. Primary URLs are listed but were not opened. Treat all of it as
secondary-verified; conflicts are flagged; UNVERIFIED means no source at all.
A GitHub Actions job (which has real network) or Het himself can re-verify any
line before it is relied on for money. Design conclusions live in `../00_DESIGN.md`.

## 1. SEBI retail algorithmic-trading framework
- Circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013, 2025-02-04, "Safer
  participation of retail investors in Algorithmic trading". Effective date moved
  2025-08-01 → 2025-10-01 → glide path; **fully mandatory for all brokers from
  2026-04-01.** NSE circulars NSE/INVG/67858 (2025-05-05), modalities 2025-07-22,
  FAQ 2025-11-03 (not opened).
- Threshold Orders Per Second (TOPS) initially **10 orders/sec** per exchange/segment.
  Client-developed algos **at or below 10 OPS need no exchange strategy
  registration**; orders carry a generic Algo ID; **static IP whitelisted by the
  broker and daily authentication still apply.** Above 10 OPS: register via broker,
  unique Algo ID. **All API orders must carry an Algo ID from 2026-04-01.**
- One static IP ↔ one client (immediate family may share with broker consent).
  Self-developed algos allowed for own/family use. Exchanges can kill-switch any Algo ID.
- White box = disclosed logic; black box = undisclosed; black-box *providers* must be
  SEBI Research Analysts. (Not applicable to self-use.)
- **Implication for this project:** a once-a-day rebalance is far below 10 OPS, so
  self-use needs only: broker API + static IP + Algo-ID tagging. No vendor registration.

## 2. F&O rule changes and SEBI outcome studies
- SEBI circular 2024-10-01: index derivative minimum contract value Rs 15 lakh
  (Nifty lot 25 → 75) from 2024-11-20; one weekly expiry per exchange (NSE kept
  Nifty weekly); upfront option premium collection from 2025-02-01; calendar-spread
  margin benefit removed on expiry day (~2025-02); intraday position monitoring
  from 2025-04-01; stricter intraday limits from 2025-10-01.
- Expiry days fixed: NSE Tuesday, BSE Thursday from 2025-09-01.
- Lot sizes revised again (NSE FAOP70616): Nifty 75 → 65, Bank Nifty 35 → 30, from
  Jan 2026 expiries (circular date UNVERIFIED).
- **Budget 2026-27 raised STT from 2026-04-01:** futures 0.02% → 0.05%; options
  premium 0.1% → 0.15%; options exercised 0.125% → 0.15%.
- Sept 2026 press: SEBI may scrap weekly expiries (no decision; UNVERIFIED).
- **Outcome studies (secondary):** FY22-24: 93% of ~1.13 crore individuals lost,
  Rs 1.81 lakh crore aggregate, avg ~Rs 2 lakh, 1% earned > Rs 1 lakh, transaction
  costs ~Rs 50,000 crore / 3 yrs, prop desks + FPIs earned Rs 33,000 + 28,000 crore
  gross in FY24 "mostly from algo use". FY25: >91% lost, Rs 1,05,603 crore. FY26
  (SEBI Aug 2026): 87.7% lost, Rs 91,685 crore, avg ~Rs 1.17 lakh, options = ~92%
  of losses, prop desks' gross profit Rs 44,483 crore.

## 3. Taxation (FY 2026-27)
- **Income-tax Act 2025 replaced the 1961 Act from 2026-04-01**; sections
  renumbered (115BBH → s.194(1) Table item 4; 194S → s.393(1) Table 8(vi); 112 → s.197);
  substance unchanged. (`factory.py` comments still cite old section numbers — a
  doc-only fix, not a math change.)
- Listed equity (STT paid): STCG 20%; LTCG 12.5% above Rs 1.25 lakh/yr; >12 months
  = long term (Finance (No.2) Act 2024, from 2024-07-23). Matches `factory.py`.
- F&O: non-speculative business income at slab rates, ITR-3; audit thresholds Rs 1
  crore / Rs 10 crore (digital) with the 6%-profit presumptive wrinkle (UNVERIFIED
  against incometax.gov.in); ICAI treats F&O turnover as absolute sum of trade P&L.
- **Crypto/VDA: 30% flat, no deductions except cost, NO loss set-off or carry-
  forward, 1% TDS on transfers.** Budget 2026-27 left both unchanged; added
  reporting penalties (Rs 200/day, Rs 50,000) for prescribed reporting entities.
- Gold ETF: STCG at slab ≤ 12 months; LTCG 12.5% > 12 months, no indexation;
  the Rs 1.25 lakh exemption does NOT apply.
- **SGB: no new tranche since Feb 2024 (2023-24 Series IV); Finance Ministry
  called it effectively discontinued.** Maturity exemption now limited to original
  subscribers (from 2026-04-01). → "gold bonds" in practice means gold ETFs.

## 4. Broker APIs (NSE), 2025-26
| Broker | Trading API | Data API | Order limit | Sandbox / paper |
|---|---|---|---|---|
| Zerodha Kite Connect | Personal plan FREE (no data) since Mar 2025 | Connect plan Rs 500/mo incl. historical | 10/sec, 5,000/day | **No sandbox** |
| Dhan (DhanHQ v2) | FREE | free with 25 trades/30d else Rs 499/mo | 10/sec, 7,000/day | **Yes** |
| Upstox | FREE | FREE | 10/sec, 500/min | Yes (place/modify/cancel only) |
| Angel One SmartAPI | FREE | free, 1 req/sec | 9/sec | UNVERIFIED |
| Fyers v3 | FREE | free | 10/sec, 100k/day | **No** |
| 5paisa | FREE | — | 600 orders/min | UNVERIFIED |
Static IP mandatory for self-coded order APIs from 2026-04-01 (all brokers).

## 5. Crypto for Indian residents
- FIU-IND registered VDASPs include WazirX, CoinDCX, ZebPay, CoinSwitch, Mudrex,
  Binance (since ~2024-08-14), KuCoin; Bybit penalised 2025-01-31 then registered.
  ~54 registered as of mid-2026 (secondary). WazirX resumed trading 2025-10-24
  after its 2024 hack and Singapore scheme.
- Public trading APIs: CoinDCX documented (2,000 req/60 s on order endpoints);
  CoinSwitch PRO, ZebPay advertise APIs; Mudrex UNVERIFIED.
- INR spot fees (conflicting, UNVERIFIED): CoinDCX 0.1-0.5%; ZebPay 0.15/0.25%;
  CoinSwitch 0.04-0.4%; Mudrex 0.45%. Plus 1% TDS on every sell.
- INR deposits: CoinDCX/CoinSwitch/ZebPay/Mudrex via UPI/IMPS/NEFT; Binance India
  only via P2P (no direct INR bank deposit).
- Free market data: Binance public REST (6,000 weight/min/IP; data-api.binance.vision)
  and WebSocket — usability from India UNVERIFIED; CoinGecko demo 10,000 calls/month;
  yfinance `BTC-USD`/`BTC-INR` coverage UNVERIFIED (→ CE-3-02 tests it on Actions).

## 6. Free NSE data
- yfinance: unofficial scraping; 429s and schema breaks (Feb 2025 redesign). Keep as
  primary only with a fallback.
- **NSE bhavcopy (UDiFF format since 2024-07-08), free, ~30-60 min after close:**
  cash `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`,
  F&O `.../content/fo/BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip`.
- `jugaad-data` (PyPI 2026-08-07) healthy, supports new NSE site + F&O; `nsepy` dead.
- **NSE weekday holidays 2026 (for phantom-day detection):** 01-26, 03-03, 03-26,
  03-31, 04-03, 04-14, 05-01, 05-28, 06-26, 09-14, 10-02, 10-20, 11-10, 11-24, 12-25
  (NSE page is the authority; verify on Actions).
- Free historical option chains: EOD bhavcopy only; intraday UNVERIFIED.

## 7. Instrument costs and rates
- Gold ETF TER (aggregators, UNVERIFIED): Nippon GoldBeES 0.69-0.81%; SBI 0.65%;
  HDFC 0.59%. GoldBeES ADV ~27-88 million units (liquid).
- Liquid ETF TER: Nippon Nifty 1D Rate Liquid BeES 0.71%; **ICICI Pru BSE Liquid
  Rate ETF 0.21%** (both UNVERIFIED).
- SEBI MF Regulations 2026 (from 2026-04-01): TER → Base Expense Ratio; index
  fund/ETF BER cap 0.90%; brokerage cap 6 bps cash / 2 bps derivatives.
- Bid-ask spreads: not published (UNVERIFIED) → measure on Actions from bhavcopy.
- **RBI repo 5.25%** (MPC decision due 2026-10-07; poll leans 25 bp hike).
  **10-yr G-sec 7.13%** (CCIL, 2026-09-25).
- G-sec / target-maturity ETF TERs: not researched (UNVERIFIED) → CE-2-01 marks UNKNOWN.

## Sources
(selected; full list retained in the worker transcript)
https://www.ncdex.com/public/uploads/circulars/Safer%20participation%20of%20retail%20investors%20in%20Algorithmic%20trading_1738763308.pdf
https://nsearchives.nseindia.com/content/circulars/INVG67858.pdf
https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQ_Retail%20Algo_03112025_NSE.pdf
https://zerodha.com/z-connect/general/a-comprehensive-overview-of-nses-circular-on-the-new-retail-algo-trading-framework
https://www.business-standard.com/markets/news/sebi-extends-retail-algo-trading-framework-rollout-to-2026-125093000956_1.html
https://www.cse-india.com/upload/upload/Oct_011024.pdf
https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf
https://www.businesstoday.in/markets/story/93-of-individual-traders-incurred-losses-in-equity-fo-during-fy22-fy24-sebi-study-447102-2024-09-23
https://openthemagazine.com/business/sebi-fo-loss-study-explained-why-9-in-10-retail-traders-lost-91685-crore-in-fy26
https://www.multibagg.ai/market-pulse/articles/budget-2026-stt-derivatives-hike-cml3r2il60004mr0j4f88ojk0
https://www.coindesk.com/markets/2026/02/02/india-s-budget-2026-keeps-crypto-taxes-tds-unchanged-adds-usd545-penalty-for-lapses
https://taxguru.in/income-tax/capital-gains-income-tax-act-2025-tax-period-2026-27.html
https://www.businesstoday.in/personal-finance/investment/story/up-to-39-tax-on-sgb-gains-investors-face-up-tough-tax-trap-after-budget-2026-clarifies-exemption-rules-514178-2026-02-02
https://upstox.com/news/personal-finance/investing/can-i-still-invest-in-the-sovereign-gold-bond-sgb-scheme/article-183870/
https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/what-are-the-charges-for-kite-apis
https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/api-sandbox
https://dhan.co/support/platforms/dhanhq-api/what-are-the-api-rate-limits-for-dhan/
https://upstox.com/developer/api-documentation/rate-limiting/
https://fyers.in/community/t/paper-trading-environment-for-fyers-api/13412
https://www.angelone.in/news/market-updates/what-s-changing-in-angel-one-s-smartapi-access-from-april-1-2026
https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2098153&reg=48&lang=2
https://coindcx-official.github.io/rest-api/
https://developers.binance.com/docs/binance-spot-api-docs
https://www.coingecko.com/en/api/pricing
https://tradingqna.com/t/has-nse-changed-bhavcopy-location/169551
https://github.com/jugaad-py/jugaad-data
https://upstox.com/stocks-market/nse-holidays/
https://www.business-standard.com/finance/news/rbi-mpc-meeting-october-2026-monetary-policy-repo-rate-hike-retail-inflation-126100200188_1.html
https://www.ceicdata.com/en/india/government-securities-yield-the-clearing-corporation-of-india-limited/ccil-government-securities-yield-10-years
https://goldenpi.com/blog/bond-news/gold-etf-expense-ratio-sbi-vs-nippon-vs-hdfc/
https://www.valueresearchonline.com/funds/1787/nippon-india-etf-nifty-1d-rate-liquid-bees/
https://cafemutual.com/news/industry/37012-sebis-new-expense-ratio-framework-here-is-what-changes-after-april-1-2026
