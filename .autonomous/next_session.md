# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him.
5. .autonomous/loop_state.json — the hourly Routine's crash/resume file.
   Read FIRST if this session is a Routine firing: `status:"in_progress"`
   means a previous firing got cut off mid-task, resume exactly from
   `resume_instructions`, never restart from scratch.
6. .autonomous/bug_log.md — known OPEN/FIXED/CLOSED defects
7. AUTONOMOUS_LOG.md (tail -40, don't read the whole thing)
8. .autonomous/operator_profile.md — before writing anything Het will
   read: plain language, why not just what, hands-off on code
9. agents/README.md — the agents/ team, hiring protocol, "code over
   tokens" pattern

## CURRENT STATE (as of 2026-08-28, commit `92a92da`)

**Phase 1, day ~39 of the 126-day minimum evaluation window** (oldest
contestants). 26 contestants (23 live on main today, 3 new ones
backfill on tomorrow's `update()`), all still rung 0 (paper), Rs 0 real
money anywhere. Zero breeding/evolution yet — both mechanisms require
`days_on_rung >= 126`, correctly not triggered this early, not a bug.

**Branch has 1 commit ahead of main**: `LOCAL_SETUP.md` (a tested local
Linux deployment guide). Het said "we'll replace it later" about
something (local vs cloud direction still being worked out) and asked
to wrap the session — **check het_directives.md for whether he answered
the "merge LOCAL_SETUP.md now?" question before assuming either way.**
Everything else built this session is already on `main`.

**This session's major work** (chronological):
- Merged Master Trader (safe/advisory version) + doc sync (PR #15, #16).
- Found and fixed `health_check.py`'s stale-local-checkout false
  positive — added `--live` flag / `live=` param, merged (PR #18,
  `4c9a60b`).
- Redesigned the check-in loop to fire **hourly** (Het asked for 15-min;
  platform hard-minimum is 1 hour, confirmed via actual API rejection).
  Built `.autonomous/loop_state.json` as the crash/resume file Het
  asked for. Old 5h routine's prompt fully rewritten with a
  crash/resume protocol, bounded-programming scope, "leave nothing
  undone," "keep NEEDS HET current" steps.
- **Declined** (logged, not built): an AI "master trader" that receives
  real capital and distributes it across strategies — Law 3 / Section
  5f kill-condition territory, needs its own dedicated conversation.
- Built the Master Trader dashboard card (advisory-only, explicitly NOT
  a P&L — it has zero authority to distribute money) after flagging
  clearly why a fabricated P&L number would be a bright-line violation.
  Merged (PR #18 batch).
- **Real strategic decision, executed**: event_drift's 0-trades pattern
  diagnosed against real price history (not guessed) — confirmed
  genuinely rare-event thresholds, not a bug. Added 3 new registry
  entries (`event_cement_t17`, `event_infra_t20`, `event_steel_t22`)
  calibrated to each leader's real 85th percentile, WITHOUT mutating
  the original 9 (Law 2 — would corrupt already-collected evidence).
  Merged (PR #19, `f53eac1`).
- Full task-log sweep (not just recent entries) — found and fixed two
  stale status markers in state.json/bug_log.md.
- Built `LOCAL_SETUP.md` for Het's planned local Linux deployment —
  every step tested in a fresh clone. On branch only pending his
  merge call.
- Verified real advisor training end-to-end for the first time
  (`parameter_bank.json` now exists on main, 5y real data).
- All 8 agents individually verified active against real live data,
  no silent failures anywhere.

## WHAT WAS LEARNED
- **The platform enforces a hard 1-hour minimum between Routine
  firings** — confirmed via actual API rejection of a 15-min cron.
  Don't try this again; hourly is the ceiling.
- **`workflow_dispatch` requires the workflow file to exist on the
  default branch (`main`) before it can be triggered via API against
  ANY ref** — confirmed via a real 404 when trying to dispatch a
  brand-new workflow against the feature branch before it was merged.
  Once merged once, subsequent dispatches against any ref work fine.
- Real price-history percentile analysis is genuinely useful for
  registry-parameter decisions (event thresholds) — grounds a
  "strategic decision" in actual data instead of a guess, and keeps it
  clearly distinguishable from Law-1-violating parameter mining (the
  distinction: calibrating to real volatility vs. reverse-engineering
  from a target trade count).
- Het has repeatedly pushed toward "make it learn/trade faster" in
  different framings (train every hour, compulsory trading, real-time
  data). Each time the honest answer has been the same underlying fact:
  the evidence clock runs on real calendar trading days, not compute
  cycles, and forcing more activity would corrupt the evidence rather
  than accelerate it. Worth recognizing the pattern quickly if it
  recurs rather than re-deriving the explanation from scratch each
  time — but still explain it fresh each time in the actual conversation,
  don't just link back to an old answer.

## WHAT REMAINS
- **LOCAL_SETUP.md merge decision** — check het_directives.md, may
  already be answered by the time you read this.
- **"openclaw"** — Het confirmed it's a real specific tool but hasn't
  named it yet. Still don't guess. Ask directly if it comes up again.
- P1-dashboard-auth — blocked_on_human, needs Het with a real browser
  (dashboard's public visibility was separately confirmed fine 2026-08-28,
  this is a different, still-open question about private-repo raw-URL auth).
- Future capital-allocation automation — parked, needs its own
  dedicated conversation if Het still wants it later.
- P2/P3 items — unchanged, low-priority/frozen per Phase 1 discipline,
  see state.json queue for exact status per item.

## EXACT NEXT TASK
1. `git fetch` + re-read `het_directives.md`'s NEEDS HET section — this
   file is a snapshot, that's live.
2. If this is a Routine firing: follow its own prompt exactly (crash/
   resume check first, health check via `--live`, bounded programming,
   leave-nothing-undone, keep NEEDS HET current).
3. If interactive with Het: normal operation, AskUserQuestion before
   anything ambiguous/costly/risky, test thoroughly, never merge
   without fresh confirmation for THAT specific change.
4. Watch for the first-ever real PROMOTE (day ~87 is the earliest any
   contestant could hit 126 days on rung from today) — flag prominently
   if it happens.

## FILES TO OPEN
- `.autonomous/state.json`, `.autonomous/het_directives.md`,
  `.autonomous/bug_log.md`, `.autonomous/loop_state.json` — living
  trackers.
- `agents/README.md` — the team, hiring protocol, "code over tokens."
- `factory.py` only if there's an actual bug to fix or a Het-confirmed
  feature to build.

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt —
  already compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only.

## TEST COMMANDS
- `python3 tools/health_check.py --live` — always use `--live` in an
  interactive session (avoids the stale-local-checkout false positive).
- Synthetic regression pattern (used for the LADDER raise and the
  event_drift recalibration): copy `factory_state/` + `factory.py` into
  an isolated scratch dir, monkeypatch `fetch_prices()` with synthetic
  data (inject occasional shock days if testing event_drift-family
  changes), run N `update()` cycles + `report()`, assert no crash and
  check new/changed entries behave correctly.
- Dashboard changes: `streamlit run dashboard.py`, then verify via a
  real headless-browser screenshot (Playwright, pre-installed at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) — don't just
  check for import errors.
- For any GitHub Actions workflow change: `workflow_dispatch` it for
  real and read the actual job logs (`mcp__github__get_job_logs`) —
  don't trust "the YAML looks right."

## EXPECTED RESULT
Phase 1 standing mode continues. Nothing should meaningfully change
session to session except accumulated ledger history, real registry-
parameter refinements grounded in real data (like the event_drift
recalibration), and genuine tooling fixes. A session wanting to
accelerate the evidence clock itself, or build toward AI-controlled
capital allocation, is violating this project's own stated discipline
— stop and flag it, don't build it.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite beyond what's already confirmed.
- You're about to merge anything to main without a fresh, specific
  confirmation for THAT change.
- You're about to build toward AI-controlled real capital allocation —
  declined explicitly, twice, needs its own dedicated conversation.
- You're about to mutate an existing live registry entry's parameters
  in place instead of adding a new one — Law 2, corrupts accumulated
  evidence.
- You're below ~20-30% of usable session context — stop, spend the
  remainder verifying and rewriting state.json/log/this file.

## OPERATOR AUTHORIZATION REQUIRED
- Any merge to main, every time, no exceptions carried forward.
- Confirming dashboard.py's private-repo raw-URL auth (needs Het, real
  browser) — separate from the public-visibility question already answered.
- Any request implying pooled/outside capital, or AI-controlled capital
  allocation.
- Deciding whether to replace cloud automation with local-only (Het is
  planning local deployment — LOCAL_SETUP.md deliberately does NOT set
  up a competing local cron, see its Section 6).

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts) and Section 9 (Strategic
  Decisions).
- The Three Laws and their authorized overrides — see state.json
  `decisions` for the full list with commit references.
- Why the event_drift recalibration added new entries instead of
  editing the originals (Law 2) — settled, see state.json's
  `event-drift-real-volatility-recalibration` decision.
- Why "make it trade/learn faster" keeps getting the same answer
  (evidence clock runs on calendar days, not compute) — settled
  reasoning, re-explain fresh each time it comes up, don't silently
  ignore a new instance of the ask.
- The platform's 1-hour Routine minimum and the workflow_dispatch
  main-branch-first requirement — both confirmed via real API errors,
  not worth re-testing.

## IMPORTANT NEW KNOWLEDGE
- The hourly loop is proven reliable now (unlike the old 5h dev-loop,
  which stays permanently disabled) — it fires, checks in, and can push
  real tested tooling fixes to the branch.
- Real advisor training has now actually run once against real data —
  `parameter_bank.json` exists on main for the first time.
- All 8 agents individually verified active against real data this
  session — if one seems broken later, that's a regression worth
  investigating, not an assumption to make lightly.
