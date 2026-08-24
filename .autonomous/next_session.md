# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him
5. .autonomous/bug_log.md — known OPEN/FIXED defects, check before
   assuming something is broken
6. AUTONOMOUS_LOG.md (tail -30, don't read the whole thing)
7. .autonomous/operator_profile.md — before writing anything Het will
   read: plain language, why not just what, hands-off on code
8. EXECUTION_PLAN.md — only if you need the phase/gate detail this file
   compresses away

## CURRENT STATE
**Phase 0 is CLEARED (2026-08-24).** All four gating deliverables
(P0-1 size-aware cost model, P0-2 post-tax expectancy, P0-3 Nifty
benchmark, P0-4 falsification criteria) are done and tested. `current_phase`
in state.json is now `"phase_1"`.

**Phase 1 = STANDING MODE** (EXECUTION_PLAN.md Section 4): run the daily
`update()` / weekly `report()` cycle, don't add new structural machinery,
let real evidence accumulate for ~12 months. The evidence clock should be
read as starting meaningfully from 2026-08-24, not earlier — the P0-1 cost
fix changed the economics underneath every prior data point.

Branch: `claude/scheduled-maintenance-template-d7yufr` (PR #1, open,
unmerged, still needs Het's fresh merge decision — see NEEDS HET below).

## WHAT WAS DONE (this session, 2026-08-24, chronological)
- P0-1 (size-aware cost model) — done earlier, commit `38dee23`.
- `agents/` team architecture (judge, researcher, breeder, risk_manager,
  reporter) — Het explicitly requested it despite a Phase 0/1-discipline
  warning, confirmed "build it anyway." Scoped narrowly: 3 of 5 are
  read-only wrappers around existing logic, 2 are new but strictly
  advisory/printed-only, wired additively into `report()`. Commit `a06e392`.
- `.autonomous/bug_log.md` and `.autonomous/het_directives.md` created per
  Het's explicit requests. Commit `99dd81b`.
- P0-2 (post-tax expectancy: STCG/LTCG-aware ranking metric, display-only,
  does not feed the verdict). Commit `ba3a0ce`.
- P0-3 (permanent Nifty buy-and-hold benchmark contestant, excluded from
  every eligibility check). Commit `ea5ac0c`.
- P0-4 verified already satisfied by EXECUTION_PLAN.md Section 5 (no code
  change needed).
- **Phase 0 gate cleared — current_phase flipped to phase_1.**

## WHAT WAS LEARNED
- **Direct evidence for the autonomous-routine-zero-commits bug**: a `git
  push` in THIS interactive session hit "claude-sonnet-5 is temporarily
  unavailable (timed out), so auto mode cannot determine the safety of
  Bash right now" — the permission classifier itself timed out. Retrying
  immediately succeeded. In an unattended Routine with nobody to notice
  and retry, this exact failure mode would look precisely like the
  observed bug: real time/token spend, clean-looking end, zero commits.
  **Still not conclusively attributed to any specific Routine firing** —
  checked `cse_01LFv3QXjUowxWUHD4XwLMym`'s session status (real activity,
  ended IDLE/REVIEW_READY), but its 18:04-18:20 UTC window overlapped this
  session's own interactive commits, and Claude Code commit authorship
  metadata is identical across all sessions, so `list_commits` can't
  disambiguate which session made which commit. See bug_log.md for the
  full trail and a concrete next-test suggestion (an isolated,
  distinctively-labeled test change fired with no interactive session
  running concurrently).
- Het gave several standing instructions this session — full list with
  status in `.autonomous/het_directives.md`. Key ones: report once daily
  (not every message) and keep working autonomously in between; commit
  and push after every tested unit of work as crash-safety (already
  standing practice); keep a bug log (done); a "fund" framing came up and
  was corrected (this is a personal paper-trading research system, NOT a
  SEBI-registrable pooled fund — don't build toward that without a
  separate explicit conversation).
- Everything else learned in prior sessions (Yahoo Finance unreachable,
  proxy auto-authenticates GitHub, GitHub Actions has real network access)
  still holds — see CLAUDE.md's "Known environment quirks."

## WHAT REMAINS
state.json `queue`:
- P0 tier: ALL DONE, gate cleared.
- P1-pr1-decision: blocked_on_human — needs Het's FRESH call on PR #1
  (merge/hold/close), a prior session's "yes" never carries forward.
- P1-dashboard-auth: blocked_on_human — needs Het, real browser, outside
  any Claude Code sandbox.
- P1-advisor-training-real-run: blocked on PR #1 merging first.
- P2/P3 items: mostly correctly low-priority/gated per Phase 1's "don't
  add machinery" guidance — see state.json for exact status per item.
- Unranked, high-value: confirm or refute the autonomous-routine-zero-commits
  bug for real (see bug_log.md's suggested test). This blocks trusting
  unattended overnight operation, which Het has repeatedly asked for.

## EXACT NEXT TASK
1. Confirm state.json's `current_phase` is still `"phase_1"` — this file
   is a snapshot, state.json is the live source.
2. **Standing mode discipline applies now**: do NOT start new features or
   structural changes on your own initiative. The daily/weekly schedule
   (factory.yml Actions workflow) is the actual mechanism accumulating
   evidence — a session's job in Phase 1 is mostly to watch, not build.
3. If picking up the routine-zero-commit investigation: fire an isolated,
   deliberately narrow, distinctively-labeled test change (e.g. a comment
   with a unique string + timestamp) via a Routine, with NO interactive
   session running at the same time, then check `list_commits` for that
   exact string. This is the only way to get an unambiguous answer.
4. If Het has replied since this was written: check his message against
   `.autonomous/het_directives.md`'s NEEDS HET section first — several
   items are already known blockers, don't re-derive them.
5. If a real PROMOTE verdict ever appears in a `report()` run: that's the
   first meaningful Phase 1 event and should be flagged prominently, not
   buried in routine logging — it's the 1->2 gate's first real data point.

## FILES TO OPEN
- `.autonomous/state.json`, `.autonomous/het_directives.md`,
  `.autonomous/bug_log.md` — the three living trackers.
- `factory.py` only if there's an actual bug to fix, not for feature work.

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt — already
  compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only, not needed for
  routine Phase 1 standing-mode sessions.
- dashboard.py — no open work item touches it right now.

## TEST COMMANDS
No committed test suite exists — all testing is ad hoc, in `/tmp`, against
synthetic monkeypatched price data (Yahoo Finance unreachable here). The
test scripts used this session (`synthetic_test.py`,
`breeding_quick_check.py`) were sandbox-local and not committed — recreate
similarly if a real code change needs verifying (unlikely in standing
mode, see EXACT NEXT TASK above).

## EXPECTED RESULT
Phase 1 standing mode: nothing should meaningfully change session to
session except accumulated ledger history. A session that finds itself
wanting to "improve" the tournament is probably violating Phase 1's own
discipline — check EXECUTION_PLAN.md Section 4 before acting on that
impulse.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite to make results look better — kill-condition
  signal per EXECUTION_PLAN.md Section 5(f). Flag it, don't act on it.
- You're about to start a new feature beyond what's already
  approved/shipped (the agents/ team) — Phase 1 says don't. Flag it to
  Het instead via het_directives.md's NEEDS HET section.
- You're below ~20-30% of usable session context — stop, spend the
  remainder verifying and rewriting state.json/log/this file.

## OPERATOR AUTHORIZATION REQUIRED
- Merging PR #1 to main (standing answer: hold off — needs a FRESH
  confirmation in a new session).
- Confirming dashboard.py's private-repo auth (needs Het, real browser).
- The LADDER rung-1 pending decision — flagged, not resolved.
- Anything that implies pooling outside money / a "fund" structure — needs
  its own dedicated conversation, SEBI registration territory.

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts) and Section 9 (Strategic
  Decisions).
- The Three Laws and their authorized overrides (advisor layer, crossover
  breeding, agents/ team) — see state.json `decisions` for the full list
  with commit references.
- P0-1/P0-2/P0-3's formulas — done, verified, documented in their own
  docstrings in factory.py.

## IMPORTANT NEW KNOWLEDGE
- Phase 0 is done. This is the biggest state change since the project's
  Phase 0 plan was written — treat every prior "wait for Phase 0" caveat
  in older docs as resolved, and read EXECUTION_PLAN.md Section 4 (not
  Section 3) as the operating mode going forward.
- `.autonomous/bug_log.md` and `.autonomous/het_directives.md` now exist
  as living trackers alongside `state.json`/`AUTONOMOUS_LOG.md` — four
  files now, each with a distinct purpose, all listed in CLAUDE.md's read
  order.
- The routine-zero-commit bug is still open and now has stronger evidence
  behind the leading hypothesis, but is still not conclusively resolved.
  Don't assume unattended operation works until it's specifically tested
  in isolation (see EXACT NEXT TASK #3).
