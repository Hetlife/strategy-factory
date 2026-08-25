# Scheduled maintenance session — 2026-08-23

Scope: item 1 from `03_learnings_and_suggestions.txt` — "Verify the Sunday
report step actually fires and produces sane output now that the cron bug
is fixed (first real Sunday run)."

## What I checked

`.github/workflows/factory.yml` currently has `schedule: - cron: "30 4 * * 0"`
and the report step's `if: github.event.schedule == '30 4 * * 0'` — these
match, so the bug described in `b003af3` ("Fix weekly report never firing")
is fixed in the workflow as it stands today.

To confirm the fix actually took effect in production (not just that the
YAML looks right), I diffed `factory_state/ledger.json` across each Sunday
commit since the fix landed (2026-08-06) against its parent commit, looking
for state changes that only `report()` can produce (promotion/demotion
verdicts, `paper_failures` increments, retirements, rung changes) as
opposed to changes `update()` produces (equity/history changes alone):

- **2026-08-09** (`5212258`): `paper_failures` incremented for
  `mom_infra_lb90` and `mom_pipes_tiles_lb90` (0 → 1). Matches a DEMOTE
  verdict on a rung-0 (paper) contestant.
- **2026-08-16** (`3ffc746`): `paper_failures` incremented for
  `mom_infra_lb60` (0 → 1). Same pattern.
- **2026-08-23** (`12d8c05`, today's run): `paper_failures` incremented for
  `mom_infra_lb40` (0 → 1) and `mom_infra_lb90` (1 → 2). Since
  `mom_infra_lb90` hit `paper_failures >= max_paper_failures` (2), it was
  correctly retired (`retired: false → true`) — this exactly matches the
  `report()` retirement logic in `factory.py`.

No promotions have occurred yet on any contestant (none has reached
`min_days_on_rung=126` with the other promotion criteria satisfied), and no
`spawn_children()` breeding has happened yet as a result — both expected at
this early stage, and consistent with rung values being unchanged (all
still 0) across every Sunday run checked.

## Verdict

**The Sunday report step is firing and producing sane, rule-consistent
output.** This is a live confirmation using real repo history, not just a
reading of the YAML — the cron fix from `b003af3` is working correctly in
production across three consecutive Sunday runs (08-09, 08-16, 08-23).

## Three Laws check

- No registry entries were added, removed, or mutated by this session.
- No code was changed — this was a read-only verification of already-committed
  automation state.
- `factory_state/ledger.json` was not touched by hand; only read via
  `git show` for diffing.

## What I did NOT do (deliberately out of scope)

- Did not touch `RULES`, `LADDER`, or `COST_PER_SIDE` (financial risk
  parameters — require Het's explicit instruction).
- Did not investigate item 2 (dashboard.py's raw-GitHub-URL auth) or item 3
  (vectorization) — scope for this session is at most one item, and item 1
  was both actionable and needed doing first since later items assume the
  automation is trustworthy.
- Noticed `train_brain.py` still has the known disconnected typo bug
  mentioned in `02_architecture.txt` (`THRESHROW_OPTIONS` on line 61) — it's
  dead code (the `'THRESHOLD_OPTIONS' in locals()` guard always evaluates
  false at module/function scope for a global, so the typo'd branch is
  never taken) and the script is not wired into `factory.py`, so it does
  not crash anything live. Left untouched — its disposition (fix vs.
  remove) is an open question for Het to decide, not a scoped item on the
  priority list.

No code changes were needed for item 1 — this note is the entire diff.
