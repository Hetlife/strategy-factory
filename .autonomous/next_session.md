# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him.
   **Also carries an active COST CONSTRAINT — read it before firing any
   new paid session/Routine.**
5. .autonomous/bug_log.md — known OPEN/FIXED defects, check before
   assuming something is broken
6. AUTONOMOUS_LOG.md (tail -30, don't read the whole thing)
7. .autonomous/operator_profile.md — before writing anything Het will
   read: plain language, why not just what, hands-off on code
8. EXECUTION_PLAN.md — only if you need the phase/gate detail this file
   compresses away

## ACTIVE CONSTRAINT — READ THIS FIRST, LITERALLY
**2026-08-25: Het asked to stop incurring extra cost and to be asked before
any further cost.** He has a Pro subscription; nobody in this project can
see his actual billing/plan details, only that `isUsingOverage: false` on
everything checked so far. Practical rule until he says otherwise: **do NOT
fire the autonomous dev-loop Routine, call `create_session`/`create_trigger`,
or otherwise spin up a new paid session without asking him first.** Normal
work inside an existing, already-running interactive session (edits,
commits, git operations, WebSearch, reading files) is fine — the
constraint is specifically about spinning up NEW sessions/Routines.

## CURRENT STATE
**Phase 0 is CLEARED (2026-08-24).** All four gating deliverables
(P0-1 size-aware cost model, P0-2 post-tax expectancy, P0-3 Nifty
benchmark, P0-4 falsification criteria) are done and tested. `current_phase`
in state.json is `"phase_1"`.

**Phase 1 = STANDING MODE** (EXECUTION_PLAN.md Section 4): run the daily
`update()` / weekly `report()` cycle, don't add new structural machinery,
let real evidence accumulate for ~12 months. The evidence clock starts
meaningfully from 2026-08-24, not earlier — the P0-1 cost fix changed the
economics underneath every prior data point.

**The 5-hourly autonomous dev-loop Routine (`trig_013GUxs9AwHaRvb1o4eGJRGx`)
is DISABLED.** It failed 4 confirmed times. A likely root cause was found
2026-08-25 (see bug_log.md) — trigger-fired sessions get no git repo
binding, unlike `create_session` calls which do. Proposed fix (make the
Routine explicitly `git clone` itself) is written but **UNTESTED** — do
not re-enable or test it without asking Het first, per the cost constraint
above.

**The daily report Routine (`trig_01Y9q1Dn98ghLMD4KX7xZfxp`, 13:00 UTC,
push-notified) is unaffected and still running.**

Branch: `claude/scheduled-maintenance-template-d7yufr` (PR #1, open,
unmerged, still needs Het's fresh merge decision — see NEEDS HET below).

A live status report for Het (redeployable, same URL) exists at:
https://claude.ai/code/artifact/c8ef2e56-3280-4141-b6fd-bc14c91333c1 —
keep it updated rather than making him read raw repo files.

## WHAT WAS DONE (2026-08-24 → 2026-08-25, chronological, latest session)
- P0-1 (size-aware cost model) — `38dee23`.
- `agents/` team (judge, researcher, breeder, risk_manager, reporter) —
  deliberate Phase 0/1-discipline override, Het explicitly confirmed
  "build it anyway." `a06e392`.
- `bug_log.md`, `het_directives.md` created per Het's request. `99dd81b`.
- P0-2 (post-tax expectancy, display-only, doesn't feed verdict). `ba3a0ce`.
- P0-3 (permanent Nifty benchmark, excluded from all eligibility checks).
  `ea5ac0c`.
- P0-4 verified already satisfied by EXECUTION_PLAN.md Section 5.
- **Phase 0 gate cleared — current_phase flipped to phase_1.** `62c549e`.
- Autonomous loop: 2 more targeted fix attempts both failed cleanly
  (no attribution ambiguity) — disabled the Routine. `1ab96eb`.
- **Root cause found via controlled comparison**: a `create_session` call
  with explicit `source_url`/`outcome_branch` committed successfully in
  under a minute; every failed Routine firing had zero repo binding.
  `a20886c`, `03850e3` (the successful diagnostic commit itself).
- Built and published a status-report Artifact for Het (see link above),
  answered 3 real open questions via AskUserQuestion (debug spend: keep
  going until fixed; LADDER rung-1: raise the rupee amount, proposed
  `[0,25k,50k,100k,200k]`, not yet implemented, needs final number sign-off;
  fund research: authorized, start now, kept separate from this repo).
- Het then asked to stop incurring extra cost without asking first — logged
  as an active constraint (see above), all further paid session/Routine
  firing paused pending his go-ahead.
- Started fund-research scoping (SEBI PMS/AIF requirements) via WebSearch
  within this same already-running session (no new paid session) — findings
  deliberately NOT committed to this repo, written to a scratch file and
  summarized in the status Artifact instead. Headline: at ₹2L capital,
  PMS (₹5cr net worth) and AIF Cat III (₹20cr corpus) are both out of
  reach by orders of magnitude — a size gap, not a paperwork gap. Informal
  pooling without registration is real legal risk, not a loophole. SEBI
  RIA registration flagged as a lower-bar route, not yet researched.

## WHAT WAS LEARNED
- **The autonomous-loop root cause is now understood, not just suspected**:
  `create_trigger` sessions carry no `sources`/`outcomes` git-repository
  binding in their `session_context` at all (verified across 4 failed
  firings), while `create_session` calls with explicit `source_url`/
  `outcome_branch` do, and that binding is what actually lets a session
  commit/push successfully. This is a structural gap in how the Routine
  was created, not a prompt-wording problem — the previous 2 "fix attempts"
  both assumed a checkout existed and only tuned retry behavior, which
  explains why neither worked.
- The classifier-timeout error ("temporarily unavailable... auto mode
  cannot determine the safety") observed interactively is real and worth
  retry-handling, but it was NOT the actual cause of the zero-commit
  pattern — ruled out by the 3rd firing (diagnostic-first, trivial task,
  still zero commits) before the repo-binding hypothesis was even tested.
- Everything else learned in prior sessions (Yahoo Finance unreachable,
  proxy auto-authenticates GitHub, GitHub Actions has real network access)
  still holds — see CLAUDE.md's "Known environment quirks."

## WHAT REMAINS
state.json `queue`:
- P0 tier: ALL DONE, gate cleared.
- **P0-5-diagnose-routine-zero-commits**: root cause found, fix proposed
  and written into the Routine's prompt already (an explicit `git clone`
  as the first action), but genuinely UNTESTED. Testing it means firing
  the Routine once more — a paid action. **Ask Het before doing this.**
- P1-pr1-decision: blocked_on_human — needs Het's FRESH call on PR #1.
- P1-ladder-rung1-raise: direction confirmed ("raise the rupee amount"),
  exact numbers proposed (`[0,25k,50k,100k,200k]`) but NOT implemented —
  needs one more explicit confirmation on the specific figures before
  editing factory.py's LADDER constant (hard-guarded risk parameter).
- P1-dashboard-auth: blocked_on_human — needs Het, real browser.
- P1-advisor-training-real-run: blocked on PR #1 merging first.
- Fund research: early scoping done (see status Artifact), SEBI RIA route
  not yet researched in depth. Findings deliberately live outside this
  repo — check the Artifact or the scratch file this session wrote,
  not `.autonomous/`.
- P2/P3 items: mostly correctly low-priority/gated per Phase 1's "don't
  add machinery" guidance — see state.json for exact status per item.

## EXACT NEXT TASK
1. Confirm state.json's `current_phase` is still `"phase_1"` and re-read
   `het_directives.md`'s cost-constraint note — this file is a snapshot,
   those are the live sources.
2. **Do not fire the autonomous dev-loop Routine, or any new paid
   session/Routine, without asking Het first.** This is the single most
   important behavioral change from this session — the cost constraint is
   active until he says otherwise, and firing the untested fix without
   asking would violate it directly.
3. If Het has given the go-ahead (check het_directives.md/the artifact's
   comment history/his own words in a live conversation): fire the Routine
   once with its current (already-updated) prompt, then verify success the
   same way this session did — `get_session` + independently checking
   `list_commits` for the actual diagnostic commit, not just trusting the
   session's own self-reported status.
4. If the fix is confirmed working: re-enable the Routine
   (`update_trigger(enabled=true)`), update bug_log.md's entry to FIXED,
   and only then consider it safe to rely on for real unattended progress.
5. Otherwise: standing-mode discipline applies — don't start new features,
   watch for a real PROMOTE (first ever, flag prominently), keep the
   status Artifact current rather than making Het read raw files.

## FILES TO OPEN
- `.autonomous/state.json`, `.autonomous/het_directives.md`,
  `.autonomous/bug_log.md` — the three living trackers.
- `factory.py` only if there's an actual bug to fix, not for feature work.

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt — already
  compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only.
- dashboard.py — no open work item touches it right now.

## TEST COMMANDS
No committed test suite exists — all testing is ad hoc, in `/tmp`, against
synthetic monkeypatched price data (Yahoo Finance unreachable here).
Recreate `synthetic_test.py`/`breeding_quick_check.py`-style scripts as
needed following the pattern already established (see prior session's
work in factory.py's `round_trip_cost()` area for the reference approach).

## EXPECTED RESULT
Phase 1 standing mode: nothing should meaningfully change session to
session except accumulated ledger history and the loop-bug investigation.
A session that finds itself wanting to "improve" the tournament (beyond
what's already authorized above) is probably violating Phase 1's own
discipline — check EXECUTION_PLAN.md Section 4 before acting on that
impulse.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite beyond the already-confirmed rung-1-raise
  direction — kill-condition signal per EXECUTION_PLAN.md Section 5(f).
- You're about to fire a new paid session/Routine without having asked
  Het first — stop, per the active cost constraint.
- You're about to start a new feature beyond what's already
  approved/shipped — Phase 1 says don't.
- You're below ~20-30% of usable session context — stop, spend the
  remainder verifying and rewriting state.json/log/this file.

## OPERATOR AUTHORIZATION REQUIRED
- Merging PR #1 to main (standing answer: hold off — needs a FRESH
  confirmation in a new session).
- Editing LADDER's rung-1 value to the proposed `[0,25k,50k,100k,200k]`
  (direction confirmed, exact figures still need explicit sign-off).
- Confirming dashboard.py's private-repo auth (needs Het, real browser).
- Firing the fixed autonomous-loop Routine to test it (cost constraint).
- Continuing fund research beyond the initial scoping (already authorized
  in principle, but check for anything more specific Het wants next).

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts) and Section 9 (Strategic
  Decisions).
- The Three Laws and their authorized overrides (advisor layer, crossover
  breeding, agents/ team) — see state.json `decisions` for the full list
  with commit references.
- P0-1/P0-2/P0-3's formulas, or the autonomous-loop root-cause diagnosis —
  all done, verified, documented with commit references. Don't re-run the
  create_session-vs-create_trigger comparison again, it's settled.

## IMPORTANT NEW KNOWLEDGE
- **Cost constraint is active** (see top of this file) — the single most
  important behavioral change this session.
- The autonomous-loop bug has a real, evidence-backed root cause now, not
  just a hypothesis — but the fix is untested, and testing costs money.
- A status-report Artifact now exists for Het specifically (link above) —
  keep it in sync with reality, it's meant to replace him having to read
  raw markdown files.
- Fund research has genuinely started, with real regulatory numbers found,
  but deliberately lives outside this repo's tracked files.
