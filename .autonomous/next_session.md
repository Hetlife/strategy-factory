# NEXT SESSION — mechanical task list (written for a low-cost model)

**Last updated: 2026-10-03.** Follow top to bottom. Don't improvise; when a
step's outcome doesn't match, stop and read the matching RUNBOOK in
`.autonomous/RUNBOOKS.md`. The Capital Engine queue
(`.autonomous/capital_engine/WORK_ORDERS.md`) is now the standing source of
substantive work; RUNBOOK 9 (Scan → Plan → Execute → Log) still wraps it.

---

## TASK 1 — Orient (~2 min)

```bash
cd /home/user/strategy-factory
git fetch origin main claude/scheduled-maintenance-template-d7yufr
git checkout claude/scheduled-maintenance-template-d7yufr && git status --short
pip install -q pandas numpy yfinance          # sandbox has none preinstalled
python3 tools/health_check.py --live
sed -n '1,40p' .autonomous/capital_engine/WORK_ORDERS.md
```
**Expected:** clean tree; `health_check: no findings.`; the index table.
If `git log --oneline -1 origin/main` already contains "Capital Engine", CE-0-01
is merged — flip its row to DONE with the SHA (if nobody has) and skip TASK 2.

## TASK 2 — Has Het said `merge CE-0-01`?

```bash
grep -n "merge CE-0-01" .autonomous/het_directives.md
```
- Found as a dated directive line (not just inside the NEEDS HET question) → do
  CE-0-01 step 4 (merge via GitHub PR, record SHA), then CE-0-02.
- Not found → do NOT merge. Say once, plainly, in your reply: the package is
  waiting on his `merge CE-0-01`. Then go to TASK 3 — do not idle.

## TASK 3 — Work that needs no merge (do these, in order)

1. `CE-2-01` — class A hypothesis document (no code). Follow the order file.
2. `CE-3-01` — class B hypothesis documents (no code).
3. `CE-1-01` — golden-master harness can be BUILT on the branch now; only its
   workflow needs `main`. Build + run it locally with the synthetic panel.
Use `/ce-workorder` for each (claim row → execute → evidence packet → flip row →
one log line → push). One order per commit.

## TASK 4 — Things that look broken but aren't (save the tokens)
- `state.json.queue` still lists P0/P1 items from 2026-09-13 with "needs merge"
  wording in their original text — the appended UPDATE lines say they merged in
  PR #22 (695ddac). Trust the UPDATE.
- `EXECUTION_PLAN.md` §9 says "Crypto → rejected" AND has a 2026-10-03 note
  reopening it as paper. Both are correct: paper only, and only after Het's A2.
- Every GATED row in WORK_ORDERS.md is supposed to stay GATED. Not a bug.
- `health_check.py` fails with `No module named numpy` → `pip install`, not a bug.

## TASK 5 — End of session
Append one line to `AUTONOMOUS_LOG.md`, update `state.json.updated_at` and
`next_action_hint`, rewrite the "Last updated" line above, write a
`/handoff-packet` if anything substantive changed, `git push -u origin
claude/scheduled-maintenance-template-d7yufr`. Never merge, never push `main`.
