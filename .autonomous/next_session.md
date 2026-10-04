# NEXT SESSION — mechanical task list (written for a low-cost model)

**Last updated: 2026-10-04.** CE-0-01 is MERGED (7866e5a, Het merged PR #23 himself); TASK 2 below is therefore already satisfied — skip it. Follow top to bottom. Don't improvise; when a
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

## TASK 2b — After Het says `merge CE-0-04` (one PR carries everything on the branch)
1. Merge via GitHub, record SHA in EVIDENCE/CE-0-04.md, add bug_log FIXED entry for phantom days.
2. Dispatch `acceleration_tools.yml` tool=`backfill-apply` on main; confirm a "Backfill nifty_benchmark history" commit lands (the 2026-10-04 attempt 403'd before the permissions fix). Mark CE-0-02 DONE.
3. Dispatch `diagnose_crypto_data.yml` on main; paste its verdict table into docs/capital_engine/research/R3_crypto_data_feasibility.md; mark CE-3-02 DONE.
4. Check Sunday 2026-10-05's factory.yml run for the skip/phantom messages (CE-0-02 step 2) and whether Friday 10-03's missing run recurs.

## TASK 2c — MILESTONE M1 in flight (started 2026-10-04, Het: "start building until major milestone")
Definition and waves: bottom of `.autonomous/capital_engine/WORK_ORDERS.md`. Wave 1 workers (side branches `ce/CE-1-04`, `ce/CE-2-03`, `ce/CE-4-02`, `ce/CE-2-04`, each off the work branch) were launched 2026-10-04. To resume: `git fetch origin`, list `ce/*` branches, read each EVIDENCE packet on its branch, re-run `python3 -m unittest discover -s tests` twice on the branch (golden fingerprint must be unchanged), then `git merge --no-ff` into the work branch ONE AT A TIME, re-running the suite after each. Resolve conflicts in tools/health_check.py (CE-1-04 vs CE-4-02 both edit it; keep both). Wave 2: CE-3-03 (branch off ce/CE-2-02: needs seed_registry_for_profile), CE-2-02b (band logic), CE-4-01, CE-4-03. Then ONE high-reasoning review of CE-2-02, CE-2-02b, CE-3-03, CE-4-02, then ONE milestone PR.

## TASK 3 — Work that needs no merge (do these, in order)

1. `CE-2-02` is BUILT on side branch `ce/CE-2-02` (NEEDS_REVIEW; read EVIDENCE/CE-2-02.md on that branch). Do NOT merge it. Next: a high-reasoning review session (see START_PROMPTS #3) after Het answers the holding-tax question in NEEDS HET. Then CE-2-02b (band logic).
1b. `CE-3-03` — class B profile `crypto` + trend signal (A2 granted; needs CE-3-02's real-run USABLE list first, which needs PR #24 merged).
1c. `CE-1-03` is DONE on the work branch, waiting for Het's `merge CE-1-03`.
1d. Next buildable now: `CE-3-03` (crypto profile; universe frozen in docs/capital_engine/research/R3_crypto_data_feasibility.md; NOTE the same holding-tax issue applies — crypto's benchmarks are BTC and cash, both permanent), `CE-1-04`, `CE-2-03`, `CE-4-02`.
2. `CE-2-03` — portfolio aggregator (read-only) once CE-1-02 is in.
3. `CE-4-03` — execution-adapter contract (document only).
(CE-1-01, CE-2-01, CE-3-01, CE-3-02 tool, CE-0-04 were done 2026-10-04.)
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
