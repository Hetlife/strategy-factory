---
name: ce-workorder
description: Execute the next Capital Engine work order (CE-x-nn) in the strategy-factory repo exactly as written, on any model including a cheap one. Use when asked to "continue the capital engine", "do the next CE order", "work the queue", or when a session has standing time and `.autonomous/capital_engine/WORK_ORDERS.md` has an OPEN order whose dependencies are DONE. Never starts a GATED order without the matching authorization line in `.autonomous/het_directives.md`.
---

# ce-workorder — pick one order, do it, prove it, hand it back

Read only what is named. Do not summarise the project. Do not redesign.

## 1. Orient (2 minutes, no judgement)
```bash
cd /home/user/strategy-factory
git branch --show-current            # expect claude/scheduled-maintenance-template-d7yufr
git status --short                   # expect clean
python3 tools/health_check.py        # expect: no findings
sed -n '1,60p' .autonomous/capital_engine/WORK_ORDERS.md
```
Pick the FIRST row with Status `OPEN` whose `Depends` are all `DONE`. If the row
says `GATED`, grep `.autonomous/het_directives.md` for the §8 sentence named in
`docs/capital_engine/00_DESIGN.md` §8; absent → skip the row, do not ask again
in the same session, and move to the next one.

## 1b. Branch check (learned 2026-10-04 the hard way)
`git branch --show-current` must print `claude/scheduled-maintenance-template-d7yufr`
before EVERY commit, not just at the start. A worker or a side-branch step can
leave HEAD elsewhere; three commits once landed on a side branch and the PR
silently lacked them until a hook caught it. If a side branch was used, merge
it into the work branch with `--ff-only` or `--no-ff`, then `git checkout` the
work branch explicitly and confirm with `git branch --show-current`.

## 2. Claim
Edit the row's Status to `IN_PROGRESS (<today>)`; commit that one-line change
(`git add .autonomous/capital_engine/WORK_ORDERS.md`). Stage by exact filename
always — never `git add -A`.

## 3. Execute exactly the order file
Open `work_orders/<ID>.md`. Touch only files under **Scope**. Anything under
**Do not touch** is a hard stop. Follow **Steps** in order. For `factory.py`
changes the test is the golden-master harness (`tests/test_golden_master.py`,
CE-1-01) plus the order's own acceptance tests; until CE-1-01 exists, use
`SESSION_PLAYBOOK.md`'s synthetic-regression recipe and paste the output.
Use `/smallest-fix` thinking: the smallest change that satisfies the acceptance
tests, with tests and error handling kept.

## 4. Stop conditions (write it down, do not improvise)
- the order is materially ambiguous; two reasonable readings → STOP
- a test fails twice for different reasons → STOP
- the change would touch `RULES`, `LADDER`, `COST_PER_SIDE`, a registry entry,
  `factory_state/ledger.json`, broker/API-key code, or derivatives logic → STOP
- anything that costs money → STOP and queue it in NEEDS HET
STOP means: set Status `BLOCKED (<one line why>)`, write the packet, commit, end.

## 5. Result packet → `.autonomous/capital_engine/EVIDENCE/<ID>.md`
```
TASK_ID: CE-x-nn
STATUS: DONE | PARTIAL | BLOCKED | NEEDS_REVIEW
EXECUTOR: <model/class>   WALL_TIME: <min>   EST_TOKENS: <n>
ACTIONS_TAKEN:
FILES_CHANGED:
TESTS_RUN:            (real commands + real output, trimmed to the relevant lines)
RESULTS:
FAILURES:
RISKS:
ASSUMPTIONS:
NEEDS_HET:            (exact question, or "none")
NEXT_RECOMMENDED_ACTION:
EXACT_RESUME_POINT:
```
Never claim DONE without pasted evidence. An exit code is not evidence.

## 6. Hand back
Flip the row to `DONE <date>, EVIDENCE/<ID>.md` (or BLOCKED), append ONE line to
`AUTONOMOUS_LOG.md`, update `.autonomous/next_session.md`'s "next action" line,
commit by filename, `git push -u origin claude/scheduled-maintenance-template-d7yufr`.
Never merge. Never push to `main`. If the order says "Fable review: YES", set
STATUS `NEEDS_REVIEW` instead of DONE and say so in the packet.
