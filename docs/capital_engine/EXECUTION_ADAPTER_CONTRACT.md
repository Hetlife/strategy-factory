# Execution adapter contract (CE-4-03, 2026-10-04)

**Status: CONTRACT ONLY. No adapter code exists, none is authorized, nothing here
is enabled or funded.** This document specifies what a *later, separately
authorized* work order must build and test. It adds no code, no dependency, no
secret. Writing it is allowed (LucyOS C9: "interfaces"); writing broker code is a
hard rule in `CLAUDE.md` and needs the exact sentences in section 11.

Sources: `00_DESIGN.md` sections 3, 5, 6, 8; `research/R2_india_regulatory_venues.md`
sections 1, 4, 5. R2 facts are secondary-verified only (its own method note);
every venue fact below must be re-verified at authorization time, before money.

---

## 1. Purpose and scope

An *execution adapter* is the single place where "the ledger says this contestant
should hold X" becomes "an order exists at a venue". It is deliberately small and
dumb: it never decides what to trade, it only carries out ledger target weights,
inside hard limits, and proves afterwards that the venue agrees with the ledger.

| Item | Decision |
|---|---|
| First adapter | `PaperAdapter` (section 9). The only one a session may build without A5. |
| Later adapters | One per venue, each implementing the same interface (section 2): one NSE broker, one crypto venue. Never one adapter spanning venues. |
| Where it sits | Downstream of `factory.py`'s ledger and `portfolio/` ceilings; upstream of nothing else. It has no write path into any ledger. |
| Who may call it | The scheduled engine step only. Agents in `agents/` stay read-only and never import it. |
| Out of scope | Choosing strategies, sizing ideas, tax filing, bank/UPI transfers, SIP (owner-only, `CE-X-03`). |

Money only ever moves for a contestant that has passed gates G1-G5 (design section 6)
including a dated `AUTHORIZE REAL CAPITAL` line. The adapter checks the same gate
state itself (section 5) and does not rely on the caller having checked.

## 2. Interface

Illustrative signatures only (a later implementer chooses the language-level
details; the behaviour below is the contract).

```text
get_positions() -> list[Position]
get_cash()      -> CashBalance
place_order(intent: OrderIntent) -> OrderResult
cancel(key: str) -> CancelResult
reconcile()     -> ReconcileReport
```

### 2.1 OrderIntent (input to `place_order`)

| Field | Type | Rule |
|---|---|---|
| `profile` | string | Profile name, e.g. `equity_nse`, `shield_nse`, `crypto_spot`. Must be an enabled profile. |
| `contestant` | string | Registry key. Must exist in that profile's ledger at rung >= 1. |
| `ticker` | string | Must be in the profile's universe (profile JSON). |
| `side` | enum `BUY` / `SELL` | No other values. No short-sell semantics: SELL may not exceed held quantity. |
| `qty` | integer (equities) or decimal at venue step size (crypto) | > 0, already rounded per section 4. |
| `limit` | decimal price | Required. Market orders do not exist in this contract. |
| `idempotency_key` | string, 64 hex chars | Computed per section 3; caller-supplied values that do not match the recomputation are refused. |
| `valid_until` | timestamp (UTC, ISO 8601) | Order is dead after this. Default end of the venue's trading day. |

### 2.2 Results and records

| Record | Fields |
|---|---|
| `Position` | `ticker`, `qty`, `avg_cost`, `as_of` |
| `CashBalance` | `currency`, `free`, `blocked`, `as_of` |
| `OrderResult` | `status` (`ACCEPTED`, `REFUSED`, `FILLED`, `PARTIAL`, `EXPIRED`, `CANCELLED`, `ERROR`), `refusal_reason` (stable code list in 5.2), `venue_order_id` (nullable), `filled_qty`, `avg_fill`, `cost_charged`, `ts` |
| `CancelResult` | `status` (`CANCELLED`, `ALREADY_FINAL`, `UNKNOWN_KEY`, `ERROR`) |
| `ReconcileReport` | `ok` (bool), `diffs` (list of `{ticker, ledger_qty, venue_qty, delta}`), `cash_diff`, `checked_at` |

### 2.3 Behavioural rules

- `place_order` is **refuse-first**: every check in sections 3 and 5 runs before any
  network call. A refusal returns `REFUSED` with a code and writes one log row; it
  never raises into the engine.
- `place_order` never retries by itself. A venue timeout leaves the order in an
  unknown state; the only legal next step is `reconcile()` (section 6), not a resend.
- `get_positions` and `get_cash` are read-only and cache nothing across runs.
- Every call appends one row to an append-only adapter log under the profile's state
  dir (key, intent, result, no secrets).

## 3. Idempotency

```text
idempotency_key = sha256( profile | contestant | ticker | date | target_weight )
```

| Part | Format |
|---|---|
| separator | a single vertical-bar character between fields, UTF-8, no padding |
| `date` | the ledger's trading date `YYYY-MM-DD` the target weight belongs to (not wall-clock) |
| `target_weight` | the ledger's weight rendered to exactly 6 decimal places, e.g. `0.083333` |

Rules:

1. The adapter keeps a durable set of keys it has ever accepted (one JSON-lines file
   in the profile's state dir; written *before* the broker call, so a crash
   mid-call cannot allow a resend).
2. A key already in the set returns `REFUSED(DUPLICATE_KEY)`. This includes keys whose
   earlier order was cancelled or expired: a new decision on the same day needs a
   different target weight, hence a different key.
3. The key is recomputed inside the adapter from the intent's fields plus the ledger
   weight; a mismatch returns `REFUSED(BAD_KEY)`.
4. Where the venue supports a client order id (tag), the key's first 20 hex chars go
   there so venue-side duplicates are also caught. Venue support is checked at
   authorization time (section 8).

## 4. Order generation

Orders come from exactly one function:

```text
orders_from_targets(ledger, profile, date, held_positions, quotes) -> list[OrderIntent]
```

Properties a test must prove:

- **Pure**: same inputs, same output; no clock, no network, no randomness, no file writes.
- **Source**: reads only the ledger's target weights for contestants at rung >= 1, the
  profile config, held positions and quotes passed in. It never accepts free text,
  model output, a chat message or an agent suggestion as an order source.
- **Delta**: order value = (target weight x contestant rung capital) minus current
  holding value, per ticker. Negative delta is SELL, but never below zero holding.
- **Minimum order value**: deltas below the profile's `min_order_value` produce no
  order (fixed costs such as `DP_CHARGE_PER_SCRIP` and 1% crypto TDS make small
  trades a net loss; the number lives in the profile JSON, not in this document).
- **Rounding**: quantity is rounded *down* to the venue's lot size (NSE cash: 1 share;
  crypto: venue step size); limit price is rounded to the venue's tick size in the
  direction that keeps the order marketable but never beyond the band below.
- **Limit orders only**: limit = last quote moved by at most `limit_band_bps` (profile
  value) against the trader (BUY above, SELL below). A stale or missing quote (older
  than the profile's `max_quote_age_s`) yields no order, not a guess.
- **Crypto sells** are generated only when the ledger target requires it; the
  generator never sells merely to rebalance inside a tolerance band, because every
  sale triggers 1% TDS and a 30% no-offset tax event (design section 7).

## 5. Limits enforced in code before any broker call

Order of checks (first failure wins; later checks are not run):

| # | Check | Source of the number | Refusal code |
|---|---|---|---|
| 1 | **Kill switch**: `factory_state/KILL` exists (global or profile dir) | file presence | `KILLED` |
| 2 | Real-money gate: contestant has a dated `AUTHORIZE REAL CAPITAL` line and gate state not RED | `het_directives.md` / `CE-4-01` evaluator | `NOT_AUTHORIZED` |
| 3 | Reconciliation ran today and was clean (section 6) | adapter log | `RECON_REQUIRED` |
| 4 | Profile enabled and ticker in universe | profile JSON | `OUT_OF_UNIVERSE` |
| 5 | Idempotency (section 3) | key set | `DUPLICATE_KEY` / `BAD_KEY` |
| 6 | Side sanity: SELL <= held qty; no negative cash result; no leverage or margin product | positions, cash | `WOULD_SHORT`, `INSUFFICIENT_CASH` |
| 7 | **Per order**: order value <= `max_order_value` | profile JSON | `ORDER_TOO_LARGE` |
| 8 | **Per day**: sum of accepted order values today <= `max_daily_value`; order count <= `max_daily_orders` | profile JSON, adapter log | `DAY_LIMIT` |
| 9 | **Per contestant hard max**: holding value after the order <= `LADDER[rung]` for that contestant's current rung (LADDER in `factory.py`, never copied into the adapter) | `factory.py` | `RUNG_CAP` |
| 10 | **Class ceilings**: class real capital after the order <= ceiling from the portfolio aggregate (A 50% floor/up to 100%, B <= 30%, C <= 20%; ceilings are maxima) | `portfolio/aggregate.py` | `CLASS_CEILING` |
| 11 | Quote freshness and limit band (section 4) | quotes | `STALE_QUOTE`, `BAD_LIMIT` |
| 12 | Venue rate: order rate stays far below the venue/SEBI threshold (R2: 10 orders/sec; a daily rebalance needs a handful) | adapter config | `RATE_LIMIT` |

### 5.1 Rules for these limits

- All numbers are read from the profile JSON or `factory.py` at call time. The
  adapter contains **no** hard-coded rupee amounts, and it never edits `RULES`,
  `LADDER` or `COST_PER_SIDE` (hard rules).
- The kill switch is checked first, on every call, by reading the file again (no
  cached result), so a KILL committed from a phone takes effect on the next call.
- A limit may only be *tighter* in the adapter than in the ledger. If the two
  disagree, the smaller number applies.
- Portfolio drawdown rules (design section 3.3: -10% B and C to paper for 90 days,
  -15% everything to A1 liquid ETF plus KILL) are evaluated by `portfolio/`; the
  adapter only honours their output (paper-only flag, KILL file).

### 5.2 Refusal code list

`KILLED, NOT_AUTHORIZED, RECON_REQUIRED, OUT_OF_UNIVERSE, DUPLICATE_KEY, BAD_KEY,
WOULD_SHORT, INSUFFICIENT_CASH, ORDER_TOO_LARGE, DAY_LIMIT, RUNG_CAP,
CLASS_CEILING, STALE_QUOTE, BAD_LIMIT, RATE_LIMIT`. New codes are added only by
amending this document.

## 6. Reconciliation

Reconciliation answers one question: does the venue hold what the ledger believes
it holds?

| Step | Rule |
|---|---|
| When | Nightly after the venue's close and settlement window, and again at the start of any run that intends to place orders. |
| Order of operations | **Reconcile first, order second.** No `place_order` is accepted (check 3 above) until today's reconcile is clean. |
| Compare | `get_positions()` versus the ledger's expected holdings per ticker; `get_cash()` versus ledger cash within a tolerance of `cash_tolerance` (profile value, covering rounding and venue fees only). |
| Position tolerance | Zero for quantity. A one-share difference is a mismatch. |
| Pending orders | An order still open at a venue counts as expected-pending, not a mismatch, until its `valid_until` passes; after that it must be resolved to filled or cancelled. |
| On any mismatch | (1) write `factory_state/KILL` with the reason and the diff table; (2) append a NEEDS HET entry to `.autonomous/het_directives.md`; (3) place no order, cancel nothing, correct nothing automatically. |
| After a mismatch | Only a human removes KILL, after investigating. The adapter never "fixes" the ledger to match the venue or the venue to match the ledger. |
| Venue unreachable / 5xx | Reconcile result is `UNKNOWN`, which is treated as not-clean: no orders, a WARN in the health check, KILL only if the condition persists past `recon_unknown_max_hours` (profile value). |

This is kill condition (i) from design section 6, with the same force as the other
kill conditions.

## 7. Secrets

- Names only appear in this repo; values never do. Naming convention (LucyOS scoped
  store): `PJ_strategy-factory__<NAME>`, for example
  `PJ_strategy-factory__<BROKER>_API_KEY`, with sibling names for the API secret and
  any access token the chosen venue requires. The exact name list is fixed in the
  authorization-time decision (section 8), not here.
- Resolved at run time from the LucyOS scoped secret store into process memory. Never
  written to the repo, to a state file, to the adapter log, to an error message or to
  stdout.
- Logs record the secret's *name* and whether it resolved, never a prefix, suffix or hash of the value.
- `aion scan` is the pre-commit gate for any adapter commit. A finding blocks the commit.
- Read-only credentials first: A5 authorizes **read-only** adapter work; order-capable
  credentials are provisioned only after A6, and scoped to the one venue.
- If the venue requires a static IP (R2 section 1, 4), the whitelisted address is
  recorded as a LucyOS-side fact and a missing or changed IP is a refusal, not a
  fallback to another route.
- The engine's daily token or session login (venues require daily authentication) is
  a LucyOS money-path step; this repo receives only the resulting short-lived token
  through the scoped store.

## 8. Venue facts and shortlist (from R2; choice deferred)

The venue is **not chosen here.** It is chosen in a dated decision written at
authorization time (when Het writes A5), after re-verifying the rows below against
the broker's own pages (R2's sources were search summaries; primary pages were not opened).

### 8.1 Regulatory facts that shape the adapter (R2 section 1)

| Fact | Consequence for the adapter |
|---|---|
| SEBI retail algo circular of 2025-02-04, fully mandatory for all brokers from 2026-04-01 | Applies from day one of any NSE live adapter. |
| At or below 10 orders/sec (TOPS), client-developed algos need no exchange strategy registration | Daily rebalance is far below this; no registration expected. Re-verify. |
| All API orders carry an Algo ID from 2026-04-01 | Adapter must pass the Algo ID the broker supplies; refuse to send an NSE order without it. |
| Static IP whitelisted by the broker; daily authentication still applies | Adapter runs from the one whitelisted address; one IP serves one client. |
| Exchanges can kill-switch any Algo ID | Treat a venue-side rejection after a kill as a reconcile trigger, not a retry. |

### 8.2 NSE broker shortlist (R2 section 4)

| Broker | Trading API cost | Order limit | Sandbox | Note |
|---|---|---|---|---|
| **Dhan** (DhanHQ v2) | free | 10/sec, 7,000/day | **yes** | Shortlisted. Data API free with 25 trades/30d, else Rs 499/mo. |
| **Upstox** | free | 10/sec, 500/min | yes (place/modify/cancel only) | Shortlisted. Data API free. |
| Zerodha Kite Connect | personal plan free, no data | 10/sec, 5,000/day | **no** | Not shortlisted: no sandbox means the live adapter could not be tested before money. |
| Fyers v3 | free | 10/sec, 100k/day | no | Same objection as Zerodha. |
| Angel One, 5paisa | free | 9/sec; 600/min | UNVERIFIED | Not shortlisted until sandbox is confirmed. |

### 8.3 Crypto venue (R2 section 5)

| Item | Fact |
|---|---|
| Eligibility | FIU-IND registered VDASP required (about 54 registered mid-2026, secondary). |
| Candidate | CoinDCX: documented public API, order endpoints about 2,000 requests per 60 s. CoinSwitch PRO and ZebPay advertise APIs; Mudrex UNVERIFIED. |
| Not a candidate | Binance India: INR funding via P2P only, no direct bank deposit. |
| Fees | Conflicting and UNVERIFIED (about 0.04-0.5% spot, by venue); measure from real fills, not from this table. |
| Tax effects on order sizing | 1% TDS on every sale and 30% flat tax with no loss set-off. The adapter's `min_order_value` for crypto must clear TDS plus fees by a wide margin; sells are generated only when the ledger requires (section 4). TDS is withheld at the venue, so the cash balance after a sell is lower than proceeds: reconcile cash against `proceeds x 0.99` plus fees, and make this a named test case. |

### 8.4 What the authorization-time decision records

Venue chosen; date; primary-source re-check of every row used; sandbox base URL
(name only); static-IP arrangement; Algo-ID mechanism; client-order-id support;
secret names (section 7); `max_order_value`, `max_daily_value`, `max_daily_orders`,
`min_order_value`, `limit_band_bps`, `max_quote_age_s`, `cash_tolerance`,
`recon_unknown_max_hours` for the profile.

## 9. PaperAdapter

`PaperAdapter` implements section 2 exactly, so a live adapter is a drop-in and
every test in section 10 runs against paper first. It is the **only** adapter a
session may build without A5, because it has no broker, no network call to a venue,
no credential and no real-money path.

| Behaviour | Rule |
|---|---|
| Fills | An accepted order fills at the **next close** after acceptance (same rule as the existing paper ledger), at that close price, only if the close satisfies the limit (BUY close <= limit, SELL close >= limit). A limit the close does not satisfy leaves the order unfilled and it expires at `valid_until`. |
| Cost | Charged through the same cost model the profile uses (size-aware `COST_PER_SIDE` path, fixed DP charge, crypto fees and 1% TDS), read from the profile, never re-implemented. |
| State | Positions and cash kept in the profile's state dir as an adapter-owned file, separate from the ledger, so reconcile compares two independent records. |
| Same refusals | Runs every check in section 5 with the same codes. Paper limits are the real limits, not looser ones; otherwise paper evidence would not predict live behaviour. |
| Cannot do | Place a live order, read a secret, import a broker SDK. A test asserts that importing the paper module pulls in no broker package. |
| Output | Same `OrderResult` and `ReconcileReport` shapes, plus `adapter: "paper"` in the log row. |

## 10. Test plan a later implementer must satisfy

All tests run against `PaperAdapter` with a fault-injecting test double for the
venue; none needs a network, a credential or real money. A live adapter is accepted
only when the same suite passes against the venue's sandbox where one exists (R2
section 4) and its read-only mode.

| # | Failure injected | Required outcome |
|---|---|---|
| T1 | **Duplicate key**: same intent submitted twice; same key after cancel | Second call `REFUSED(DUPLICATE_KEY)`; exactly one venue order; key persisted before the call (crash-between test: restart and resend is still refused) |
| T2 | **Partial fill** then expiry | `PARTIAL` recorded with true filled qty; next target computation uses actual holdings; no top-up order under the same key; reconcile clean |
| T3 | **Stale quote** (older than `max_quote_age_s`, or missing) | No order generated; if forced into `place_order`, `REFUSED(STALE_QUOTE)` |
| T4 | **Broker 5xx / timeout** on `place_order` | `ERROR`, no automatic resend, key stays consumed, next step is `reconcile()`; run is not marked clean until it passes |
| T5 | **Reconciliation mismatch** (venue holds one share more or less) | `factory_state/KILL` written with diff table, NEEDS HET entry appended, zero orders placed afterward, ledger byte-identical to before |
| T6 | **Kill switch**: KILL appears between two orders of one run | Second order `REFUSED(KILLED)`; kill read fresh each call |
| T7 | **Limits**: order above per-order max; day total exceeded; holding above `LADDER[rung]`; class over ceiling; SELL above holding | One test each; correct code; no venue call (assert call count zero) |
| T8 | **Order generation purity**: same inputs twice; ledger with rung-0 contestants; free-text "buy X" | Identical output; rung-0 contestants produce nothing; no code path accepts text |
| T9 | **Rounding**: sub-lot quantity; off-tick price; below min order value | Rounded down to lot; tick-rounded within band; no order below minimum |
| T10 | **Crypto sell with TDS**: sell proceeds credited minus 1% | Cash reconcile passes with the TDS rule and fails if TDS is ignored |
| T11 | **Secrets**: run with every log and state file captured | No secret value appears anywhere (planted canary value); `aion scan` clean; missing secret gives a refusal, not a crash |
| T12 | **Golden master**: engine run with adapter disabled | Ledger bytes identical to the pre-adapter golden master (`CE-1-01`) |
| T13 | **Wrong-venue guard**: paper module import | No broker SDK imported; no network socket opened |

Also required: the adapter log is append-only (a test tries to rewrite it), and a
10-day paper soak with injected faults ends with reconcile clean and zero KILLs that
were not deliberately injected.

## 11. Authorization sentences Het must write first

Copied verbatim from `00_DESIGN.md` section 8. Nothing carries forward from any
earlier grant; a session copies the sentence into `.autonomous/het_directives.md`
with the date when he writes it.

| # | Unlocks | Sentence Het writes |
|---|---|---|
| A5 | Any broker/exchange adapter code, read-only first (hard rule: broker/execution/API-key code) | `AUTHORIZE BROKER ADAPTER READ-ONLY <broker>` |
| A6 | Real capital for one contestant in one class, after CE-4-01 shows AMBER | `AUTHORIZE REAL CAPITAL <class> <contestant> <amount>` |

Order of use: A5 first (read-only adapter, sandbox where one exists), then A6 per
contestant (order-capable credentials, one venue, one contestant, one amount).
Without A5 only `PaperAdapter` and this document may exist. The text above is the
whole authorization; a session must not treat any other message as equivalent.

## 12. Explicit non-goals

- No automatic transfers, no SIP, no bank or UPI integration (owner-only, `CE-X-03`).
- No leverage, margin or borrowed funds, in any class.
- No shorting; SELL never exceeds a held quantity.
- No options or futures (class C stays gated behind A4 and its own order, `CE-X-01`).
- No market orders; every order is a limit order with a band and an expiry.
- No intraday strategy support; the contract assumes at most a daily rebalance.
- No free-text, chat or agent-originated orders.
- No automatic retry, automatic correction of a mismatch, or automatic removal of KILL.
- No second scheduler, approval system or secret store (LucyOS D-1).
- No change to `RULES`, `LADDER`, `COST_PER_SIDE`, or any registry entry.
