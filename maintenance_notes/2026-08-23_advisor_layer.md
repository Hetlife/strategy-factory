# Advisor layer + evolutionary tier — 2026-08-23

This is a large, explicitly authorized feature, not a routine scoped-maintenance
item — built at Het's direct request in an interactive session, after I flagged
that it overrides two of the project's own "Three Laws" and got explicit
sign-off on each point (see the in-session Q&A this commit follows).

## What this adds

1. **`advisors.py`** — a monthly-run training script. Downloads 5y of history
   for the existing `UNIVERSE` tickers, backtests a mechanism-bounded
   parameter grid (same ranges the seed registry already uses) through the
   *same* `sig_*` functions `factory.py` runs live (no separate/divergent
   backtest logic), and scores every candidate with three independent
   "advisor" heuristics — a team, not one grid-search winner:
   - `sharpe_advisor` — full-period risk-adjusted return
   - `robustness_advisor` — min(first-half, second-half) Sharpe, directly
     encoding lesson #3 from `03_learnings_and_suggestions.txt` (the stat-arb
     regime-break collapse) so a parameter set that only worked in one regime
     scores poorly
   - `cost_efficiency_advisor` — net return per round trip, encoding lesson #2
     (costs dominate at high turnover)

   The three heuristics are rank-averaged into one ensemble score per
   `(strategy family, sector)` bucket, and the top 5 per bucket are written to
   `factory_state/parameter_bank.json`.

2. **`factory.py` — advisor-informed evolution, in `report()`.** Every live
   contestant is ranked tournament-wide (same order the leaderboard already
   uses). Any contestant that is:
   - on the **paper tier only** (`rung == 0`) — real-money-rung contestants
     are explicitly excluded; they still only evolve through the existing
     `spawn_children()` breeding-on-promotion path,
   - ranked **outside the top 10**,
   - and has already cleared the existing evaluation bar
     (`RULES["min_days_on_rung"]`, `RULES["min_trades"]` — I reused these
     rather than inventing a new financial-risk-adjacent threshold),

   gets retired, and a **new** registry key is created with its numeric
   hyperparameters blended toward the advisor bank's top pick for its family
   (`mutate_params`). This is a mutation in the *behavioral* sense you asked
   for, but mechanically it still never edits an existing registry dict entry
   in place — Law 2's actual technical invariant (`spawn_children()` never
   mutates the parent) is preserved; the "combined bank from each parent" you
   asked for is `parameter_bank.json` itself, since its entries are
   backtested independent of any single live contestant's history and every
   family's bank draws from the whole seed grid, not one parent's params.

3. **Trust weight — "how much to listen to the advisor," decided
   collectively.** `factory_state/advisor_state.json` holds a single
   `trust_weight` (0.05–0.9, starts at 0.25) used as the blend weight in
   `mutate_params`. Each `report()` run, every lineage child that has
   finished its own evaluation window is scored against the parent it
   replaced (`update_advisor_trust`); if most beat their parent's mean
   return, `trust_weight` nudges up by 0.05, otherwise down. This is a
   tournament-wide, evidence-based vote across all evolved children so far,
   not a single strategy's opinion.

4. **`.github/workflows/advisor_training.yml`** — new monthly cron
   (1st of month, 7:00 AM IST) that runs `advisors.py train` and commits
   `parameter_bank.json`, mirroring the existing `factory.yml` pattern
   (concurrency-locked, rebase-and-push, full history checkout).

5. **`dashboard.py`** — new "Advisor Layer" section: trust-weight metric +
   history chart, and the full parameter bank ranked table. The leaderboard
   table gained a `Lineage` column (`seed` vs `🧬 advisor-evolved from X (gen N)`)
   and an `Evolved out` status for contestants retired by this mechanism
   (distinct from a rule-based `Retired`, so the two are never conflated in
   the UI).

## Backward compatibility

`blank_stats()` now includes `lineage`, `evolved_out`, `trust_scored` fields.
`load_state()` backfills these onto every contestant already in
`ledger.json` on load (`setdefault`), so the existing 20-contestant ledger
loads and runs without a KeyError. Verified locally.

## Three Laws — explicit deviations, both authorized this session

- **Law 1** ("hypotheses mined from data are forbidden"): `advisors.py`
  is exactly that — backtesting a parameter grid against historical price
  data and ranking by backtest performance. Deliberately overridden per your
  answer to "raw historical price data." Mitigations kept in place anyway:
  grids stay inside the same mechanism-bounded ranges the seed registry
  already uses (no unbounded scan), and the robustness advisor specifically
  penalizes regime-break fragility, per this project's own prior research.
- **Law 2** ("never mutate a live strategy"): evolution *behaviorally*
  replaces an underperforming paper-tier contestant's parameters. Mitigation
  I chose without asking again: never applied to a real-money-rung
  contestant — only ever to paper tier. Flagging this explicitly in case you
  want it to apply more broadly later.

## What I tested

Yahoo Finance is unreachable from this sandbox (network policy blocks it —
same as it would for the unmodified `factory.py`), so I could not run a live
`python factory.py update` / `report` or `python advisors.py train` against
real data. Instead, against a **copy** of `factory_state/` (never the live
ledger):
- Monkeypatched `fetch_prices()`/`fetch_history()` with a synthetic random-walk
  price panel and ran `factory.py update()` (~20 cycles) and `report()`
  end-to-end — no crashes, sane promote/hold/demote/retire output.
- Ran `advisors.py train()` against synthetic 600-day history — produced a
  7-bucket parameter bank, no crashes.
- Forced contestants into evolution-eligible state (`days_on_rung=200`,
  `trades=50`) and re-ran `report()` — confirmed advisor-evolved children
  were correctly created only for rung-0, outside-top-10 contestants, with
  lineage recorded, and `advisor_state.json` written.
- Launched `dashboard.py` with `streamlit run` locally and loaded it in a
  real browser (Playwright/Chromium) against the actual GitHub `main`
  branch's raw ledger — confirmed the existing leaderboard/equity chart
  still render correctly, the new `Lineage` column shows `seed` for all
  current contestants, and the new Advisor Layer section renders its
  correct pre-first-run empty states (`parameter_bank.json` and
  `advisor_state.json` don't exist on `main` yet, so it shows "waiting for
  first run" messages rather than erroring).

## What I noticed but did not fix (pre-existing, out of scope)

`report()`'s Sharpe calculation floors variance at `1e-12`
(`var = max(sum_sq/n - mean**2, 1e-12)`). With very few trades and
near-canceling returns this can blow up to an absurd Sharpe (seen in the
synthetic test: values like 106512 or -110393). This exists in the current
`main` code, unrelated to this change, and given real trade counts/return
distributions it's unlikely to bite in production the way it did with a
20-day synthetic sample — flagging it rather than fixing it inside an
already-large PR.
