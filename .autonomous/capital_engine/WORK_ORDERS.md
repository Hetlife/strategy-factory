# Capital Engine — work-order index

**For any session, on any model.** Pick the first order whose status is OPEN
and whose dependencies are DONE, read ONLY that order file plus the files it
names, do it, write the result packet to `EVIDENCE/<ID>.md`, flip the status
here, append one line to `AUTONOMOUS_LOG.md`. Procedure: `.claude/skills/ce-workorder/SKILL.md`.
Design/why: `docs/capital_engine/00_DESIGN.md`. Never start a GATED order
without the matching §8 sentence in `.autonomous/het_directives.md`.

| ID | Title | Executor | Depends | Fable review | Status |
|---|---|---|---|---|---|
| [CE-0-01](work_orders/CE-0-01.md) | Merge the work branch to `main` | OWNER | — | NO | OPEN — PR #23 open (needs Het: `merge CE-0-01`) |
| [CE-0-02](work_orders/CE-0-02.md) | Run ACCELERATION_PLAN steps 2-4 on `main` | CLAUDE_CODE | CE-0-01 | NO | OPEN |
| [CE-0-03](work_orders/CE-0-03.md) | Retire-never-traded decision packet | CLAUDE_CODE + OWNER | CE-0-02 | NO | OPEN |
| [CE-1-01](work_orders/CE-1-01.md) | Golden-master regression harness | CLAUDE_CODE | CE-0-01 | NO | OPEN |
| [CE-1-02](work_orders/CE-1-02.md) | Profile loader (one engine, N classes) | CLAUDE_CODE | CE-1-01 | YES | OPEN |
| [CE-1-03](work_orders/CE-1-03.md) | Per-profile workflow matrix | CLAUDE_CODE | CE-1-02 | NO | OPEN |
| [CE-1-04](work_orders/CE-1-04.md) | Health harness per class | CLAUDE_CODE | CE-1-02, CE-1-03 | NO | OPEN |
| [CE-2-01](work_orders/CE-2-01.md) | Class A hypothesis doc (Law 1) | CLAUDE_CODE → OWNER sign | — | NO | OPEN |
| [CE-2-02](work_orders/CE-2-02.md) | `shield_nse` profile + fixed-weight signal | CLAUDE_CODE | CE-1-02, CE-2-01 signed | YES | OPEN |
| [CE-2-03](work_orders/CE-2-03.md) | Portfolio aggregator (read-only) | CLAUDE_CODE | CE-1-02, CE-1-03 | NO | OPEN |
| [CE-3-01](work_orders/CE-3-01.md) | Class B hypothesis docs (Law 1) | CLAUDE_CODE → OWNER sign | — | NO | OPEN |
| [CE-3-02](work_orders/CE-3-02.md) | Crypto data feasibility on Actions | CLAUDE_CODE + DET | CE-0-01 | NO | OPEN |
| [CE-3-03](work_orders/CE-3-03.md) | `crypto` profile + trend signal (paper) | CLAUDE_CODE | CE-1-02, CE-1-03, CE-3-01, CE-3-02, **§8 A2** | YES | GATED (A2) |
| [CE-4-01](work_orders/CE-4-01.md) | Capital activation gates evaluator | CLAUDE_CODE | CE-2-03 | NO | OPEN |
| [CE-4-02](work_orders/CE-4-02.md) | Kill switch file | CLAUDE_CODE | CE-1-01 | YES | OPEN |
| [CE-4-03](work_orders/CE-4-03.md) | Execution-adapter contract (doc only) | CLAUDE_CODE | CE-4-01 | YES | OPEN |
| [CE-5-01](work_orders/CE-5-01.md) | LucyOS project definition | FABLE (this session) | — | — | DONE 2026-10-03 (LucyOS PR open, unmerged) |
| [CE-5-02](work_orders/CE-5-02.md) | Evidence sync into LucyOS money path | CLAUDE_CODE (LucyOS repo) | CE-5-01 | NO | OPEN |
| [CE-X-01](work_orders/CE-X-01.md) | Class C (F&O) paper — design complete | CLAUDE_CODE | A, B producing evidence, **§8 A4** | YES | GATED (A4) |
| [CE-X-02](work_orders/CE-X-02.md) | Broker adapter, read-only first | CLAUDE_CODE | CE-4-03, CE-4-01 AMBER, **§8 A5** | YES | GATED (A5) |
| [CE-X-03](work_orders/CE-X-03.md) | SIP from other projects (owner finance) | OWNER | sevaa M1, class A GREEN | — | GATED (owner) |

Parallel-safe today (no dependency on the merge): CE-2-01, CE-3-01 (documents).
Everything in CE-1 can be built on the branch before CE-0-01 but its workflow
tests only run after the merge.

**Status values:** OPEN · IN_PROGRESS (<session date>) · DONE <date, evidence file> · BLOCKED (<why>) · GATED (<§8 item>).
