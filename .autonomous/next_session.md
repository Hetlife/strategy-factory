# NEXT SESSION — mechanical task list (written for a low-cost model)

**Last updated: 2026-09-02.** Follow this top to bottom, in order. Don't
skip steps, don't improvise. If a step's outcome doesn't match what's
written, stop and read `.autonomous/RUNBOOKS.md`'s matching RUNBOOK
rather than guessing.

---

## TASK 1 — Orient (exact commands, ~2 min)

```bash
cd /home/user/strategy-factory
cat .autonomous/loop_state.json
git fetch origin main
git status --short
python3 tools/health_check.py --live
```

**Expected:** `loop_state.json` status `"idle"`. `git status --short`
empty. `health_check.py --live` prints `health_check: no findings.`
(exactly that line, nothing else) — as of 2026-09-02 it is fully clean.

If `health_check` prints any `[WARNING]` or `[ERROR]`: read
`.autonomous/RUNBOOKS.md` Step 1.3/1.3a for the decision table. Do not
dismiss a warning without doing the check it asks for.

If `loop_state.json` says `"in_progress"`: resume exactly from its
`resume_instructions` field. Do not restart from scratch.

---

## TASK 2 — Confirm the merge is real (exact commands)

The promotion-bar fix (Q5) and breeding gate (Q6) merged to `main` on
2026-09-02 via PR #21, commit `bc4b07f`. Confirm it's actually there —
don't just trust this file:

```bash
grep -n "require_beat_benchmark" factory.py
grep -n "promotion_check" agents/judge/judge.py
```

**Expected:** both commands print matching lines. If either prints
nothing, STOP — something is wrong, escalate via RUNBOOK 6, do not try
to re-apply the fix yourself.

---

## TASK 3 — Routine check-in (RUNBOOK 1)

Run `.autonomous/RUNBOOKS.md` RUNBOOK 1, top to bottom, exactly as
written. It covers: the daily/weekly workflow status, the free
supervisor, and whether any contestant has ever been promoted (there
should be none yet — day 40+ of 126).

**If nothing changed:** say "Nothing new" in 1-2 sentences and stop.
Do not manufacture work — Phase 1's correct amount of new machinery is
approximately zero.

---

## TASK 4 — If Het is present, one question only

Ask once, plainly, don't repeat if already answered this session:

> "The new promotion bar is live on `main` now. Want me to look into Q4
> next — whether any contestant actually beats Nifty net of costs?"

- If yes → this is a bigger research task (needs judgment, not
  mechanical steps), better suited to a stronger model. Tell Het that
  and offer to flag it rather than attempting it here.
- If no / not present → do nothing further, go to TASK 5.

---

## TASK 5 — End cleanly

```bash
git status --short
git log --oneline -1
```

If nothing to commit, stop here. If you changed a tracker file
(`AUTONOMOUS_LOG.md`, `.autonomous/state.json`,
`.autonomous/het_directives.md`), stage by exact filename (never
`git add -A`), commit, and push to
`claude/scheduled-maintenance-template-d7yufr` — never to `main`
without Het's fresh, in-session "yes" for that specific change.

---

## DO NOT (hard stops, no exceptions)

- Do not change `RULES`, `LADDER`, or `COST_PER_SIDE`. The 2026-08-30
  authorization was for exactly two named changes and is spent.
- Do not merge or push to `main` without asking fresh, every time.
- Do not add options/futures/margin/leverage/broker code.
- Do not invent a new trading strategy on your own initiative.
- Do not claim a test passed without actually running it.
- If you're unsure whether something needs a bigger/more expensive
  model's judgment (research questions, ambiguous requests, anything
  touching money or RULES): say so and stop, rather than guessing.

---

## Reference (read only if something looks broken)

- `.autonomous/RUNBOOKS.md` — full mechanical procedures, decision
  tables, "STOP and escalate" points.
- `MASTER_PLAN.md` — why the promotion bar mattered, what's next (Q4).
- `docs/research/Q5_statistical_power.md` /
  `Q6_breeding_overfitting.md` — the finished analysis behind the merge.
- `.autonomous/het_directives.md` → NEEDS HET section — anything still
  waiting on him.

## Current state, verified 2026-09-02

- Phase 1, day 40+ of 126. 26 live contestants, all rung 0 (paper),
  Rs 0 real money, zero promotions ever.
- **Promotion bar fix is LIVE on `main`** (merged, verified, health
  check clean). Next scheduled weekly `report()` run uses it for real.
- Q4 (does anything beat Nifty net of cost/tax) is the next research
  question — unblocked, not started, needs a session with more
  reasoning budget than a mechanical task list can specify in advance.
