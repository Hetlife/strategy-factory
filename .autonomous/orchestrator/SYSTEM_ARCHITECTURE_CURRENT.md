# System Architecture — Current State (audited 2026-09-13)

Read-only audit, no assumptions carried from prior sessions. Every claim
below was checked against the live repo/GitHub state on this date.

## Code (4,328 lines of Python total)

| File | Lines | Role |
|---|---|---|
| `factory.py` | 1,045 | Core engine: `update()` (daily P&L/positions), `report()` (weekly Sharpe/drawdown/PROMOTE-DEMOTE-retire verdicts, advisor-informed evolution), `promotion_check()`/`excess_return_stats()`/`multiplicity_sharpe_floor()` (the Q5/Q6 statistical gate, merged 2026-09-02). |
| `dashboard.py` | 706 | Streamlit read-only view, reads GitHub raw URLs. Never a write path. |
| `advisors.py` | 187 | Monthly training script; backtests a mechanism-bounded parameter grid through the live `sig_*` functions; writes `factory_state/parameter_bank.json`. Law-1 override, authorized. |
| `agents/*` (8 subpackages) | ~660 combined | `judge` (99 lines, delegates to `factory.promotion_check`), `reporter` (83), `hr` (157), `master_trader` (149), `risk_manager` (105), `researcher` (50), `breeder` (40), `healer` (74). All real_money_exposure=0. |
| `tools/*` (11 scripts) | ~1,400 combined | `health_check.py` (253, the live verifier), `supervisor_check.py` (113), `analyze_statistical_power.py` (252, drives the real `promotion_check`), `analyze_q4_vs_benchmark.py` (212), plus one-off diagnostics (Nifty100 list/tickers, event thresholds, monsoon history, dashboard state builders). |

No test suite exists (`find . -name "test_*.py"` returns nothing). The
project's testing convention instead is: write a small deterministic
script under `tools/`, run it for real against synthetic or live data,
and log the actual output in `AUTONOMOUS_LOG.md`/`bug_log.md` — see
`SESSION_PLAYBOOK.md`'s testing standard.

## State/data

- `factory_state/ledger.json` — `registry` (27 keys) + `contestants` (27
  entries). Schema per contestant: `rung, days_on_rung, equity, peak,
  positions, trades, days_in_market, sum_ret, sum_sq, paper_failures,
  retired, history, lineage, evolved_out, trust_scored`. Never hand-edited.
- `factory_state/advisor_state.json` — self-tuning `trust_weight`.
- `factory_state/parameter_bank.json` — advisor training output.
- `.autonomous/state.json` — structured live-state tracker (queue,
  decisions, phase, recent commits). 23 queue items as of this audit, 0
  currently blocking automation.
- `.autonomous/loop_state.json` — crash/resume file for any multi-step
  session task. Currently the only piece of "orchestration state" that
  exists anywhere in this project.

## Automation (all free, deterministic GitHub Actions — no paid model in the loop)

| Workflow | Schedule | Last verified run (this audit) |
|---|---|---|
| `factory.yml` | Mon–Fri 12:45 UTC (`update()`), Sun 04:30 UTC (`report()`) | run #58, success, committed `Factory update 2026-09-11` |
| `supervisor.yml` | every ~2h | run #124, success, 2026-09-13 05:22 UTC |
| `advisor_training.yml` | monthly | last real run 2026-08-27, succeeded |
| `diagnose_*` (3 workflows) | manual `workflow_dispatch` only | not on a schedule, one-off diagnostics |

Zero promotions to date: `rung > 0` count in the live ledger is 0 out of
27 contestants; 15 of 27 have never traded (0 trades). This is expected
under Phase 1's evidence-accumulation window, not a fault.

## Paid-model automation

One Routine: `trig_01Y9q1Dn98ghLMD4KX7xZfxp`, hourly, model
`claude-sonnet-5`, runs RUNBOOK 9 (Scan → Plan → Execute → Log). This is
the only "agent" that runs unattended; there is no multi-agent runtime,
no persistent process, no OpenClaw/LucyOS integration, and no local
model in this project's actual automation — those were researched for
Het's personal PC setup but never wired into `strategy-factory` itself.

## What does NOT exist (confirmed absent, not merely undocumented)

- No token/cost accounting mechanism (manual model choice only).
- No dedicated "verifier" subsystem beyond `health_check.py --live`
  (deterministic) and ad-hoc adversarial subagent reviews (new as of
  this pass — see `VERIFICATION_PROTOCOL.md`).
- No persistent multi-agent orchestrator process. The 2026-08-based
  5-hourly autonomous dev-loop Routine that attempted something like
  this failed 5 confirmed times and was abandoned by Het's own decision
  (`state.json` queue item `P0-5`).
- No CI test suite; correctness is established per-change via targeted
  scripts and real (not asserted) execution, logged in `bug_log.md`.
