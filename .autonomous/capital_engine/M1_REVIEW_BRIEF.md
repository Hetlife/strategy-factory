# Milestone M1 — review brief (for ONE high-reasoning review session)

Read ONLY this file, `docs/capital_engine/00_DESIGN.md` §2-3 and §8, and the diffs named below. State on the work branch `claude/scheduled-maintenance-template-d7yufr` at the time of writing: 106 tests OK twice; equity golden fingerprint `fbedc106...e075` unchanged since the monsoon_cement retirement; only `equity_nse` enabled (`python3 tools/list_enabled_profiles.py` -> `["equity_nse"]`); all gates RED (`python3 tools/gates_report.py`).
Command to see everything new vs main: `git diff origin/main...HEAD --stat` and `git diff origin/main...HEAD -- factory.py`.

## What to approve or reject (each: APPROVE / REJECT with the reason; smallest fixes only)
| Order | What | Where to look | The question |
|---|---|---|---|
| CE-2-02 | `sig_fixed_weight`, `seed_registry_for_profile`, `profiles/shield_nse.json` (disabled) | factory.py three hunks; profile JSON | Is the signal long-only, gross 1.0, never negative? Does `load_state` seed from the profile ONLY for non-default profiles? |
| CE-2-02b | `fixed_weight_next` + one `update()` branch | factory.py `def fixed_weight_next`, `if params["fn"] == "fixed_weight"` | Orchestrator verified: day return is booked from yesterday's positions BEFORE the branch (no double drift); only rebalances are costed; only that fn is affected. Confirm no path can change an equity contestant. |
| CE-3-03 | `sig_trend_long_flat`, `sig_cash`, `post_tax_expectancy_vda`, two `update()` branches, `profiles/crypto.json` (disabled) | factory.py; profile JSON; B1 hypothesis | Does the signal match B1 §3 (Donchian excludes today; SMA includes today; strict `>`; half weight for 2x-BTC vol; never short)? Is the VDA tax display-only (no verdict)? |
| CE-4-02 | kill switch: `kill_switch_active`, early return in `update()`/`report()`/`advisors.train()`, backfill refuses `--apply` under KILL, workflow status steps | factory.py top of `update`/`report`; advisors.py; tests/test_kill_switch.py | Can any write path still run while a KILL file exists? (Known: none in the repo; workflow steps only print.) |
| CE-4-03 | execution-adapter contract (document only) | docs/capital_engine/EXECUTION_ADAPTER_CONTRACT.md §5, §6 | Is the check order safe (kill first, authorization, reconciliation, then limits)? Is "venue unreachable = UNKNOWN, KILL only after a persistence window" acceptable? |

## Already reviewed by the orchestrator (Sonnet), no further action unless you disagree
CE-1-03 (merged to main), CE-1-04, CE-2-03, CE-2-04, CE-4-01, CE-5-02 (LucyOS, merged).

## Known limitations to rule on (not fixed; each needs an owner call or a gated order)
1. **Promotion pairs against the first permanent benchmark only** (CE-3-03b, GATED). For class B that is BTC buy-and-hold; B1 §4 also requires beating cash, post-tax. No non-equity profile may be enabled with rules until fixed.
2. **Paper holding tax (0.13%/week) vs class A's cash benchmark** — the per-profile setting exists (CE-2-04); Het has not yet answered "exempt class A" or "keep". With the tax, A's kill test (A1 §6) trips by construction.
3. **Cash baseline stats**: `positions` stay empty so days_in_market/Sharpe show 0/NaN; equity and returns are correct (display only).
4. **Trend/shield contestants hold weights without drift between rebalances** (trend) — the engine's existing simplification.
5. **Supervisor is stricter**: any warning (including a KILL file or CLAUDE.md-hash drift) now turns the 15-minute run red.
6. **Gate G3 treats class A as floor 50% / cap 100%** (fixed from a 50% max); G4 reaches AMBER at most; GREEN never acts.

## After approval
Open ONE PR from the work branch to main titled "Milestone M1: Capital Engine paper-ready". Merge sentence for Het: `merge M1`. After merge: dispatch `supervisor.yml` once and confirm the per-profile loop; profiles stay `enabled: false` (Het's A3 sentences enable them one at a time).
