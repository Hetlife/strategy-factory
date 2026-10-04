# Milestone M1 — review record (Sonnet-level, 2026-10-04)

**Reviewer: Claude Sonnet 5.5 (the orchestrating session), at Het's instruction "Start doing sonnet task".
This is NOT the stronger-model review `M1_REVIEW_BRIEF.md` recommended.** It is a careful second look using real runs, and the PR says so. Het decides whether that is enough before `merge M1`; the brief remains available for a later high-reasoning pass at any time (it costs one session).

State reviewed: work branch `claude/scheduled-maintenance-template-d7yufr`; 108 tests OK (run twice); equity golden fingerprint unchanged; only `equity_nse` enabled; `python3 tools/gates_report.py` RED for A, B, C.

| Order | Verdict | Evidence (what was actually run or read) |
|---|---|---|
| CE-2-02 `sig_fixed_weight`, `seed_registry_for_profile` | APPROVE | Read the three factory.py hunks: long-only, weights renormalised to gross 1.0, `{}` when nothing present; profile seeding applies only when `FACTORY_PROFILE != equity_nse`. 9 tests. Equity registry fns are `event_drift 12, momentum 10, input_cost 3, monsoon 1, benchmark 1` — none of the new ones, so no equity contestant can reach the new code. |
| CE-2-02b band rebalancing | APPROVE | Read `update()`: `day_ret` is booked from yesterday's stored positions BEFORE the branch (no double drift); the branch re-bases turnover on drifted weights so only a rebalance is costed; keyed on `fn == "fixed_weight"` only. Fail-closed if the cash ETF is missing. 7 tests incl. one-rebalance-per-ISO-week. |
| CE-3-03 crypto signal + VDA tax + cash baseline | APPROVE with one limitation | Direct run of `sig_trend_long_flat` for all 6 variants (donchian/sma x 50/100/200) on a synthetic up/flat/down panel: never negative, gross <= 1, flat and falling coins excluded. `post_tax_expectancy_vda` is called only in the report's display columns (lines ~1233-1260), never in a verdict. Limitation (CE-3-03b, gated): promotion pairs against the first permanent benchmark only. 17 tests. |
| CE-4-02 kill switch | APPROVE | **End-to-end proof** on a scratch copy of the repo: with `factory_state/KILL` present, `factory.py update`, `factory.py report`, `advisors.py train` and `tools/backfill_benchmark_history.py --apply` each printed the KILL notice and changed nothing — sha256 of every file under `factory_state/` identical before and after. Static audit of every non-test writer (`save_state`, `save_json`, `json.dump`, `open(..., "w")`): all ledger/market-log/advisor-state/parameter-bank writes sit inside `update()`, `report()`, `advisors.train()` or the backfill apply path, each guarded. Remaining writers are derived or local (portfolio `--write` summary, trading-floor JSON, dashboard notes, HR scaffolder) and do not touch the ledger. Workflows only print KILL status; the Python entry points stop. |
| CE-4-03 adapter contract (document only) | APPROVE | 329 lines, exactly two files changed, no code, no secret-shaped strings; A5/A6 sentences verbatim from design §8; check order kill -> authorization -> reconciliation -> limits is safe; unreachable venue = not clean. R2 venue facts are secondary-verified and must be re-verified at A5 time. |

## Found and fixed during this review
1. **Empty price download crashed with a bare IndexError** (pre-existing, found by the kill-switch release test in the sandbox where Yahoo is blocked). `update()` now prints a plain notice and exits 1 (run goes red, nothing written). +2 tests, golden unchanged.
2. **Class A ceiling** was wrongly a 50% maximum in the aggregator; the design says floor 50% / cap 100%. Fixed earlier today with tests.

## Residual risks a stronger model could still examine (none blocks `merge M1` because every new profile is disabled)
- The trend/shield strategies hold weights without drift between rebalances (the engine's existing simplification).
- Supervisor strictness: any warning now turns the 15-minute run red.
- Cash-baseline stats (Sharpe NaN, days_in_market 0) are display-only.
- The two limitations in the brief that need Het: holding tax for class A, and CE-3-03b.

## What `merge M1` does and does not do
Merging changes what runs live in exactly three ways: the daily/Sunday workflows run through `discover` (already live since PR #26) plus the kill-switch status step; `update()` gains the kill-switch early return and the empty-download failure; the monitor now checks per enabled profile. **No new profile is enabled, so no new ledger is created and no class B/C/shield contestant exists live.**
