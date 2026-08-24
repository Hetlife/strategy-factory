# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, Phase 0 pointer,
   `.autonomous/operator_profile.md` pointer)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. AUTONOMOUS_LOG.md (tail -30, don't read the whole thing)
5. .autonomous/operator_profile.md — before writing anything Het will
   read: plain language, why not just what, hands-off on code
6. EXECUTION_PLAN.md — only if you need the phase/gate detail this file
   compresses away

## CURRENT STATE
Phase: Phase 0 (EXECUTION_PLAN.md Section 3) — instrumentation before
  evidence, before any capital.
Gate: 0->1. Blocked on P0-2, P0-3, P0-4 (P0-1 is done — see below).
Objective: ship the remaining Phase 0 deliverables on the existing
  branch, test each against synthetic data, never merge to main.
Evidence: 35 days live paper history (as of 2026-08-24), 20 contestants
  (1 retired), equity range 0.876-1.011 under the OLD cost model. Zero
  promotions. No edge demonstrated. Phase 0 is instrumentation work, not
  evidence-accumulation — don't expect these numbers to move meaningfully
  until Phase 1, and note the historical ledger still reflects the OLD
  flat-rate cost model until someone re-runs it (see P0-1 below).
Branch: claude/scheduled-maintenance-template-d7yufr (PR #1, open,
  unmerged).

## WHAT WAS DONE
- Wrote and committed three strategy documents (understanding.txt,
  pivot_document.txt, mission_document.txt), condensed into
  EXECUTION_PLAN.md, plus AUTONOMOUS_OPERATING_SYSTEM.txt (session
  protocol) and this next_session.md handoff format.
- state.json queue rewired to Phase 0 (P0 tier gates everything below).
- Added .autonomous/operator_profile.md — Het's communication/goal
  preferences from a direct Q&A, kept separate from any verbatim
  conversation content (deliberately not logged into this repo).
- **P0-1 DONE (commit `38dee23`).** Replaced flat `COST_PER_SIDE` with
  `round_trip_cost(turn, tickers_sold, effective_capital)` in both
  `factory.py` and `advisors.py` — variable cost (0.222% RT) + a FIXED
  Rs 15.34 DP charge per scrip sold. Paper-tier (rung 0) contestants are
  costed against `LADDER[1]` as a stand-in basis (LADDER[0]=Rs 0 would
  divide by zero, and rung 1's economics are what the promotion decision
  actually depends on). Verified against EXECUTION_PLAN.md's own
  acceptance criterion exactly (1.1424%, target 1.1-1.15%). Full
  synthetic regression suite passes; confirmed several contestants'
  equity trajectories visibly shift under the corrected model, as
  expected — this was NOT re-run against the real committed
  `factory_state/ledger.json` (that only happens for real inside the
  scheduled `factory.yml`/`advisor_training.yml` GitHub Actions runs,
  which have real network access this sandbox doesn't).

## WHAT WAS LEARNED
- **The autonomous Routine has an undiagnosed problem.** Three separate
  scheduled/fired sessions today (`cse_01Da9uY9SmjfvPrtmqRdvqsp`,
  `cse_01H9tf7znTkhumTLS1a43YVt`, `cse_011vKmzRq7AFukbm7GxoaBVm`) each
  ran for real (6-11 minutes, real token spend, `SESSION_STATUS_IDLE`/
  `REVIEW_READY` on completion — not a crash) but produced ZERO commits
  each time, despite unblocked, well-specified P0 queue items sitting
  right there. P0-1 above was done INTERACTIVELY instead, specifically
  to avoid a fourth blind firing. **If you are an autonomous firing of
  this Routine reading this: you may be about to repeat this pattern.
  Before ending your session, check — did you actually run `git commit`
  and `git push`, or did you only investigate/plan? If the latter, that
  is very likely the bug: some combination of tool-permission friction,
  over-caution, or losing the thread across the READ FIRST steps is
  causing sessions to "work" without ever committing.** Diagnosing this
  properly (not just re-firing and hoping) is now a live investigation —
  see EXACT NEXT TASK below.
- COST_PER_SIDE's fix is done; see WHAT WAS DONE. P0-2 (post-tax
  expectancy) is the next concrete, well-specified, code-level task.
- The tournament currently ranks strategies on pre-tax returns only. A
  6-month-hold strategy taxed at 20% STCG and a 13-month-hold strategy
  taxed at 12.5% LTCG (with a Rs 1.25L/yr exemption that can zero out an
  entire year's tax on this capital base) are not comparable on Sharpe
  alone. This is P0-2, not yet in code.
- This sandbox's outbound proxy transparently authenticates GitHub
  requests (GH_TOKEN=proxy-injected) — do not re-attempt to verify
  dashboard.py's private-repo auth with a curl/requests call from inside
  a Claude Code session; it will falsely appear to succeed.
- Yahoo Finance is unreachable from every Claude Code sandbox used on
  this project so far. All code-level testing must use synthetic/
  monkeypatched price data and say so explicitly.

## WHAT REMAINS
state.json `queue`, priority "P0":
  P0-1-size-aware-cost-model — DONE (38dee23)
  P0-2-post-tax-expectancy — open
  P0-3-nifty-benchmark — open
  P0-4-falsification-criteria-committed — open, but likely already
    substantively satisfied by EXECUTION_PLAN.md Section 5 existing —
    verify that claim rather than assuming, then mark done if so
Everything below P0 in the queue stays frozen until the P0-GATE item
clears (current_phase flips "phase_0" -> "phase_1" in state.json).

Plus the new, unranked item from "What was learned": diagnose why the
autonomous Routine keeps working without committing. This isn't in
state.json's queue yet as a formal ID — add one (e.g.
`P0-5-diagnose-routine-zero-commits`) if you pick it up, since it's
arguably now higher-value than P0-2/P0-3 given it blocks unattended
operation entirely.

## EXACT NEXT TASK
1. Open state.json, confirm current_phase and P0 item statuses — this
   file is a snapshot from 2026-08-24, state.json is the live source.
2. If you're an interactive session: pick P0-2 or P0-3 next (either
   order, both independent of each other and of P0-1). For P0-2: add a
   post-tax expectancy metric to report()'s output, using <=12mo hold
   -> 20% STCG, >12mo -> 12.5% LTCG minus Rs 1.25L/yr exemption. Resolve
   the exemption-aggregation question (it's account-wide and annual, not
   per-strategy) explicitly before wiring it into any promotion logic —
   this is exactly the kind of thing that could silently double-count or
   under-count if rushed. For P0-3: add a permanent Nifty buy-and-hold
   contestant to the same ledger/daily cycle, explicitly excluded from
   demotion/retirement/evolution eligibility checks (grep for where
   propose_evolutions()/attempt_breeding() filter candidates and add the
   same exclusion there).
3. If you're an autonomous/scheduled firing: seriously consider making
   your first action a SMALL, deliberately trivial change (e.g. a
   one-line log/state update) purely to test whether you can actually
   get to `git commit && git push` at all in this environment, before
   attempting a real P0 item. If even that fails, that's your diagnosis
   — report it precisely (what command, what error/behavior) in this
   file's next rewrite rather than silently ending again.
4. Once a P0 item is done and tested: update state.json (status ->
   "done", add commit sha, update next_action_hint), append one
   AUTONOMOUS_LOG.md line, rewrite this file's relevant sections.
5. Once ALL FOUR P0 items are done and tested: flip current_phase to
   "phase_1", unfreeze P1/P2/P3 queue items, STOP starting new feature
   work — Phase 1 (EXECUTION_PLAN.md Section 4) is standing mode.

## FILES TO OPEN
- factory.py (P0-2, P0-3 both touch this; P0-1's `round_trip_cost()` is
  already there as a reference for the established pattern of "verify
  against EXECUTION_PLAN.md's own acceptance criterion before trusting
  it")
- EXECUTION_PLAN.md Section 3 (exact P0-2/P0-3/P0-4 specs)
- .autonomous/state.json (queue status, source of truth for what's done)

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt — their
  substance is already compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only.
- dashboard.py — not touched by any remaining P0 item (P0-2's
  per-contestant metric surfaces in report()'s own output first;
  dashboard display is a natural P1 follow-up, not P0).

## TEST COMMANDS
No committed test suite exists yet — all testing is ad hoc, in /tmp,
against synthetic monkeypatched price data (Yahoo Finance unreachable
here). Pattern established by P0-1: monkeypatch `factory.fetch_prices()`/
`advisors.fetch_history()`, run the relevant function through several
cycles, and directly assert the computed value against a hand-worked
example matching EXECUTION_PLAN.md's stated acceptance criterion — don't
just check "it doesn't crash."

## EXPECTED RESULT
P0-2/P0-3: additive — should not change any existing verdict's PROMOTE/
DEMOTE outcome, only add new metrics/contestants/documentation. If a
change to either one changes an existing verdict, that's a sign it's
doing more than it should — stop and reconsider before committing.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite (not just P0-1's already-done formula shape)
  to make results look better — that's a kill-condition signal per
  EXECUTION_PLAN.md Section 5(f). Flag it, don't act on it.
- A P0 item requires a product/values decision that can't be inferred
  (e.g. exactly how to display post-tax expectancy when holding period
  is ambiguous) — mark it blocked_on_human in state.json and move to the
  next open item rather than guessing.
- You're below ~20-30% of usable session context — stop starting new
  work, spend the remainder verifying and rewriting state.json/log/this
  file.

## OPERATOR AUTHORIZATION REQUIRED
- Merging PR #1 to main (standing answer: hold off — needs a FRESH
  confirmation in a new session, a prior "yes" does not carry forward).
- Merging P0-1's (or any) COST_PER_SIDE-shape change to main
  specifically, even fully tested, because it changes every historical
  verdict.
- Confirming dashboard.py's private-repo auth (needs Het, real browser,
  outside any Claude Code sandbox).
- The LADDER rung-1 pending decision (raise it vs. restrict rung-1 to
  1-2 names) — flagged, not resolved, not to be resolved autonomously.

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts 1-11) and Section 9
  (Strategic Decisions Already Made).
- The Three Laws and their authorized overrides (advisor layer, paper P&L
  crossover breeding) — see AUTONOMOUS_TODO.md Decisions Made for full
  rationale if needed, don't re-litigate whether they should exist.
- P0-1's cost formula derivation — it's done, verified, and documented in
  `round_trip_cost()`'s own docstring in factory.py. Don't re-derive it;
  extend it if a real bug is found.

## IMPORTANT NEW KNOWLEDGE
- The Routine's zero-commit pattern (see WHAT WAS LEARNED) is the single
  most important open problem right now — more important than P0-2/P0-3
  individually, because it determines whether this project can actually
  run unattended at all. Don't let it get lost under routine task
  bookkeeping.
- Three-tier session-continuity system now exists: AUTONOMOUS_OPERATING_
  SYSTEM.txt (protocol, immutable unless Het asks to revise), EXECUTION_
  PLAN.md (compressed operational map), this file (literal handoff). Keep
  all three in sync — Phase-0-meaning changes go in EXECUTION_PLAN.md,
  routine progress goes in state.json + this file, not the OS doc.
- .autonomous/operator_profile.md now exists — read it before writing
  anything Het will read directly.
