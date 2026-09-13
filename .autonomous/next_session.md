# NEXT SESSION — mechanical task list (written for a low-cost model)

**Last updated: 2026-09-03.** Follow this top to bottom, in order. Don't
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
(exactly that line, nothing else) — as of 2026-09-03 it is fully clean.

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

## TASK 4 — If Het is present, raise the two open decisions

Q4 was answered 2026-09-03 (`docs/research/Q4_beat_nifty.md`). Two
things are waiting on Het. Raise them once, plainly, don't nag, and
don't re-ask if he already answered this session:

> "Two things from the Q4 analysis. First: the promotion clock
> effectively restarted — the new bar compares each strategy against the
> Nifty benchmark day-by-day, and the benchmark only started recording
> on 26 Aug while the strategies started 13 July. So nothing can be
> promoted until the benchmark catches up, about six weeks later than
> we thought. I'd recommend just accepting that. Second: 15 of the 26
> strategies have never traded once in 44 days — their thresholds never
> get crossed. Do you want those loosened, or left as rare-event
> insurance?"

- Both are **his** calls. Do not change thresholds, do not touch the
  ledger, do not "fix" the clock yourself.
- If he's not present → leave them flagged, go to TASK 5.

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
- `MASTER_PLAN.md` — why the promotion bar mattered, and the ranked
  list of what's left.
- `docs/research/Q4_beat_nifty.md` — the benchmark-clock finding.
- `docs/research/Q5_statistical_power.md` /
  `Q6_breeding_overfitting.md` — the finished analysis behind the merge.
- `.autonomous/het_directives.md` → NEEDS HET section — anything still
  waiting on him.

## Current state, verified 2026-09-03

- Phase 1, day 40+ of 126. 26 live contestants, all rung 0 (paper),
  Rs 0 real money, zero promotions ever.
- **Promotion bar fix is LIVE on `main`** (merged, verified, health
  check clean). Next scheduled weekly `report()` run uses it for real.
- **Q4 is ANSWERED** (2026-09-03): nothing beats Nifty yet — 0 of 25 at
  95% confidence — but only 4-7 days are actually usable, so that is
  "cannot measure yet", not "failed". See `docs/research/Q4_beat_nifty.md`.
- **Nothing can be promoted right now**, by design: the benchmark has
  too little history to certify against, so the gate fails closed with
  "cannot certify". This is correct, not a bug. Do not try to fix it.
- Remaining open research questions are Q3, Q7, Q8, Q9 — all lower value
  than simply letting the calendar run. See `MASTER_PLAN.md`'s table.
