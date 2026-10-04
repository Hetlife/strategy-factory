# Capital Engine — work-order index

**For any session, on any model.** Pick the first order whose status is OPEN
and whose dependencies are DONE, read ONLY that order file plus the files it
names, do it, write the result packet to `EVIDENCE/<ID>.md`, flip the status
here, append one line to `AUTONOMOUS_LOG.md`. Procedure: `.claude/skills/ce-workorder/SKILL.md`.
Design/why: `docs/capital_engine/00_DESIGN.md`. Never start a GATED order
without the matching §8 sentence in `.autonomous/het_directives.md`.

| ID | Title | Executor | Depends | Fable review | Status |
|---|---|---|---|---|---|
| [CE-0-01](work_orders/CE-0-01.md) | Merge the work branch to `main` | OWNER | — | NO | DONE 2026-10-04, merge 7866e5a (Het merged PR #23 himself), EVIDENCE/CE-0-01.md |
| [CE-0-02](work_orders/CE-0-02.md) | Run ACCELERATION_PLAN steps 2-4 on `main` | CLAUDE_CODE | CE-0-01 | NO | DONE 2026-10-04, EVIDENCE/CE-0-02.md — backfill applied on main (aa0ad36, benchmark 61 rows); Sunday-skip observation 2026-10-05 is the last loose end |
| [CE-0-03](work_orders/CE-0-03.md) | Retire-never-traded decision packet | CLAUDE_CODE + OWNER | CE-0-02 | NO | DONE 2026-10-04: Het "if it's failing remove it" → `RETIRED_BY_OWNER` in factory.py — MERGED to main via PR #25; effective first daily run |
| [CE-0-04](work_orders/CE-0-04.md) | Phantom-day guard in `update()` (21% fake days, measured) | CLAUDE_CODE | CE-1-01 | YES | DONE 2026-10-04 — MERGED to main (PR #24, Het), EVIDENCE/CE-0-04.md |
| [CE-1-01](work_orders/CE-1-01.md) | Golden-master regression harness | CLAUDE_CODE | CE-0-01 | NO | DONE 2026-10-04 (Sonnet built, Fable reviewed: fresh-state design approved, CI-missing-golden now fails), EVIDENCE/CE-1-01.md; first CI run pending |
| [CE-1-02](work_orders/CE-1-02.md) | Profile loader (one engine, N classes) | CLAUDE_CODE | CE-1-01 | YES | DONE 2026-10-04 (Sonnet built on `ce/CE-1-02-profiles`, Fable reviewed + merged into the work branch 42dc01f; 14 tests OK, golden unchanged), EVIDENCE/CE-1-02.md — MERGED to main via PR #25 (75907a1, Het) |
| [CE-1-03](work_orders/CE-1-03.md) | Per-profile workflow matrix | CLAUDE_CODE | CE-1-02 | NO | DONE 2026-10-04 (Sonnet built, reviewed: 22 tests OK twice, YAML parsed, equity crons/guard/prefix unchanged), EVIDENCE/CE-1-03.md — MERGED to main via PR #26 (Het, 2026-10-04 05:37 UTC, ae6d534). First real run (manual dispatch 37180428638): discover ok, weekend leg skipped, equity leg started; result recorded below once complete |
| [CE-1-04](work_orders/CE-1-04.md) | Health harness per class | CLAUDE_CODE | CE-1-02, CE-1-03 | NO | OPEN |
| [CE-2-01](work_orders/CE-2-01.md) | Class A hypothesis doc (Law 1) | CLAUDE_CODE → OWNER sign | — | NO | DONE 2026-10-04, A1_shield_core.md, Het: "3 approved" |
| [CE-2-02](work_orders/CE-2-02.md) | `shield_nse` profile + fixed-weight signal | CLAUDE_CODE | CE-1-02, CE-2-01 signed | YES | NEEDS_REVIEW 2026-10-04 — built on side branch `ce/CE-2-02` (9deabdc, packet 73b157c; 24 tests OK twice, equity golden unchanged, profile disabled). NOT merged. Two design problems for Fable/Het BEFORE it merges or is ever enabled: (1) no band logic (stateless sig, daily free rebalancing flatters the sleeve); (2) PAPER_HOLDING_TAX_WEEKLY would make shield_core trail its own exempt cash benchmark by ~6.5%/yr, tripping A1's kill test by construction |
| [CE-2-03](work_orders/CE-2-03.md) | Portfolio aggregator (read-only) | CLAUDE_CODE | CE-1-02, CE-1-03 | NO | OPEN |
| [CE-3-01](work_orders/CE-3-01.md) | Class B hypothesis docs (Law 1) | CLAUDE_CODE → OWNER sign | — | NO | DONE 2026-10-04, docs/capital_engine/hypotheses/B0,B1 (Het may veto before CE-3-03) |
| [CE-3-02](work_orders/CE-3-02.md) | Crypto data feasibility on Actions | CLAUDE_CODE + DET | CE-0-01 | NO | DONE 2026-10-04 — real run: 12/12 USABLE, universe frozen (R3), EVIDENCE/CE-3-02.md |
| [CE-3-03](work_orders/CE-3-03.md) | `crypto` profile + trend signal (paper) | CLAUDE_CODE | CE-1-02 (PR #25), CE-1-03, CE-3-01, CE-3-02 | YES | OPEN — all inputs ready (A2 granted, B1 signed, universe frozen in R3); build after PR #25 merges |
| [CE-4-01](work_orders/CE-4-01.md) | Capital activation gates evaluator | CLAUDE_CODE | CE-2-03 | NO | OPEN |
| [CE-4-02](work_orders/CE-4-02.md) | Kill switch file | CLAUDE_CODE | CE-1-01 | YES | OPEN |
| [CE-4-03](work_orders/CE-4-03.md) | Execution-adapter contract (doc only) | CLAUDE_CODE | CE-4-01 | YES | OPEN |
| [CE-5-01](work_orders/CE-5-01.md) | LucyOS project definition | FABLE (this session) | — | — | DONE 2026-10-04 — LucyOS PR #96 MERGED by Het (04:49 UTC); money_path.json now live in LucyOS |
| [CE-5-02](work_orders/CE-5-02.md) | Evidence sync into LucyOS money path | CLAUDE_CODE (LucyOS repo) | CE-5-01 | NO | DONE 2026-10-04 (Sonnet built, reviewed: gates re-run independently, 11 tests OK, authority strict+anti-dup ok, scan clean) — MERGED to LucyOS main via PR #97 (Het, 2026-10-04 05:37 UTC); nightly maintenance now runs the sync; EVIDENCE/CE-5-02.md |
| [CE-X-01](work_orders/CE-X-01.md) | Class C (F&O) paper — design complete | CLAUDE_CODE | A, B producing evidence, **§8 A4** | YES | GATED (A4) |
| [CE-X-02](work_orders/CE-X-02.md) | Broker adapter, read-only first | CLAUDE_CODE | CE-4-03, CE-4-01 AMBER, **§8 A5** | YES | GATED (A5) |
| [CE-X-03](work_orders/CE-X-03.md) | SIP from other projects (owner finance) | OWNER | sevaa M1, class A GREEN | — | GATED (owner) |

Parallel-safe today (no dependency on the merge): CE-2-01, CE-3-01 (documents).
Everything in CE-1 can be built on the branch before CE-0-01 but its workflow
tests only run after the merge.

**Status values:** OPEN · IN_PROGRESS (<session date>) · DONE <date, evidence file> · BLOCKED (<why>) · GATED (<§8 item>).
