# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, Phase 0 pointer)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. AUTONOMOUS_LOG.md (tail -30, don't read the whole thing)
5. EXECUTION_PLAN.md — only if you need the phase/gate detail this file compresses away

## CURRENT STATE
Phase: Phase 0 (execution_plan/EXECUTION_PLAN.md Section 3) — instrumentation
  before evidence, before any capital.
Gate: 0->1. Blocked on P0-1 through P0-4 (state.json `queue`, priority "P0")
  all being done AND tested.
Objective: ship the four Phase 0 deliverables on the existing branch, test
  each against synthetic data, never merge to main.
Evidence: 35 days live paper history (as of 2026-08-24), 20 contestants (1
  retired), equity range 0.876-1.011. Zero promotions. No edge demonstrated.
  This has not materially changed since Phase 0 work started — Phase 0 is
  instrumentation work, not evidence-accumulation work, so don't expect the
  evidence numbers to move until Phase 1.
Branch: claude/scheduled-maintenance-template-d7yufr (PR #1, open, unmerged).

## WHAT WAS DONE
- Wrote and committed three strategy documents (understanding.txt,
  pivot_document.txt, mission_document.txt) analyzing cost model, tax
  treatment, asset-class choice, and the realistic path from Rs 2L to a
  large sum.
- Condensed those into EXECUTION_PLAN.md — the operational reference with
  Phase 0-4 gates, kill conditions, and the P0-1..P0-4 task list.
- Committed AUTONOMOUS_OPERATING_SYSTEM.txt (this session-protocol spec)
  and wired .autonomous/state.json's queue to Phase 0 (P0 priority tier
  added above P1/P2/P3; everything below P0 marked frozen_until_phase1
  except items already blocked_on_human, which aren't phase-gated).
- Updated CLAUDE.md to point sessions at EXECUTION_PLAN.md and the new
  Phase 0 gate.
- Built the full advisor/breeding layer (crossover breeding, paper P&L
  display) in prior sessions — see AUTONOMOUS_TODO.md Decisions Made for
  full rationale; not re-summarized here.

## WHAT WAS LEARNED
- COST_PER_SIDE=0.0019 (flat 0.38% round trip) understates real Indian
  equity delivery costs by up to ~3x at the position sizes LADDER rung 1
  actually implies (~Rs 1,667/position in a 6-name basket -> true cost
  ~1.14% RT, not 0.38%). This is a live correctness defect, not yet fixed
  in code — it's P0-1.
- The tournament currently ranks strategies on pre-tax returns only. A
  6-month-hold strategy taxed at 20% STCG and a 13-month-hold strategy
  taxed at 12.5% LTCG (with a Rs 1.25L/yr exemption that can zero out an
  entire year's tax on this capital base) are not comparable on Sharpe
  alone. This is P0-2, also not yet in code.
- This sandbox's outbound proxy transparently authenticates GitHub
  requests (GH_TOKEN=proxy-injected) — do not re-attempt to verify
  dashboard.py's private-repo auth with a curl/requests call from inside
  a Claude Code session; it will falsely appear to succeed. See
  state.json queue item P1-dashboard-auth for what's actually needed.
- Yahoo Finance is unreachable from every Claude Code sandbox used on
  this project so far. All code-level testing must use synthetic/
  monkeypatched price data and say so explicitly.

## WHAT REMAINS
Everything in state.json's `queue` with priority "P0" and status "open":
  P0-1-size-aware-cost-model
  P0-2-post-tax-expectancy
  P0-3-nifty-benchmark
  P0-4-falsification-criteria-committed (likely already substantively
    satisfied by EXECUTION_PLAN.md Section 5 existing — verify, don't
    just assume; consider breaking it into its own small tracked file if
    that fits better)
Everything below P0 in the queue is frozen until the P0-GATE item clears
(current_phase flips from "phase_0" to "phase_1" in state.json).

## EXACT NEXT TASK
1. Open state.json, confirm current_phase is still "phase_0" and re-check
   which P0 items are marked "open" vs "done" — don't trust this file's
   memory of that over state.json, which is the live source.
2. Pick the first "open" P0 item in numeric order (P0-1 first, unless a
   prior session already closed it — check state.json, not assumption).
3. For P0-1 specifically: implement round_trip_cost_pct(position_size) =
   0.222% + (Rs 15.34 / position_size) in factory.py, replacing the flat
   COST_PER_SIDE usage in the cost-charging line inside update(). Verify
   the split across buy/sell sides correctly (the DP charge is a
   sell-day-only fixed charge per EXECUTION_PLAN.md P0-1's note — don't
   naively halve it). Test: a 6-name rung-1 basket (~Rs 1,667/position)
   must price at ~1.1-1.15% round trip, not 0.38%. Then re-run every
   existing ledger verdict against the corrected model with synthetic
   data and record what changes (this doubles as Q1 in the research
   backlog). Draft/test on this branch only — do not merge to main
   without Het's fresh, explicit, in-session confirmation, even though
   drafting is pre-authorized by EXECUTION_PLAN.md's own Phase 0 text.
4. Once a P0 item is done and tested, update state.json (flip its status
   to "done", add the commit sha), append one AUTONOMOUS_LOG.md line, and
   move to the next open P0 item if session budget allows.
5. Once ALL FOUR P0 items are done and tested: flip state.json's
   current_phase to "phase_1", unfreeze the P1/P2/P3 queue items (remove
   the "_frozen_until_phase1" suffix from their status where applicable),
   and STOP starting new feature work — Phase 1 (EXECUTION_PLAN.md
   Section 4) is standing mode: run the schedule, touch nothing
   structural, let time accumulate real evidence.

## FILES TO OPEN
- factory.py (P0-1, P0-2, P0-3 all touch this)
- EXECUTION_PLAN.md Section 3 (exact P0-1..P0-4 specs)
- .autonomous/state.json (queue status, source of truth for what's done)

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt — their
  substance is already compressed into EXECUTION_PLAN.md; only open one
  if you need the full arithmetic behind a specific claim.
- AUTONOMOUS_TODO.md — narrative decision rationale only; not needed for
  Phase 0 implementation work.
- dashboard.py / advisors.py — not touched by any P0 item.

## TEST COMMANDS
No committed test suite exists yet (all testing this session and prior
sessions has been ad hoc, in /tmp, against synthetic monkeypatched price
data, since Yahoo Finance is unreachable from this sandbox). For P0-1:
monkeypatch factory.fetch_prices() with a synthetic price panel, run
update()/report() through several cycles, and directly assert the
round-trip cost charged for a known position size matches the expected
formula output before/after the change.

## EXPECTED RESULT
P0-1: existing ledger verdicts may change once the corrected cost model
is applied retroactively (this is expected and should be reported, not
treated as a bug). P0-2/P0-3/P0-4: additive — should not change any
existing verdict, only add new metrics/contestants/documentation.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite (not just its formula shape) to make results
  look better — that impulse is itself a kill-condition signal per
  EXECUTION_PLAN.md Section 5(f). Flag it, don't act on it.
- A P0 item turns out to require a product/values decision that can't be
  inferred (e.g., how to display post-tax expectancy when a contestant's
  holding period is ambiguous) — mark it blocked_on_human in state.json
  and move to the next open item rather than guessing.
- You're below ~20-30% of usable session context — stop starting new
  work and spend the remainder verifying, updating state.json, appending
  to AUTONOMOUS_LOG.md, and rewriting this file for the session after you.

## OPERATOR AUTHORIZATION REQUIRED
- Merging PR #1 to main (standing answer: hold off, asked twice, needs a
  FRESH confirmation in a new session — do not treat a prior "yes" as
  live).
- Merging any P0-1 (COST_PER_SIDE-shape) change to main specifically,
  even once tested, because it changes every historical verdict.
- Confirming dashboard.py's private-repo auth (needs Het to check the
  raw ledger URL in a real incognito browser — no sandbox session can do
  this itself, see "What was learned" above).
- The LADDER rung-1 pending decision (raise it, or restrict rung-1
  strategies to 1-2 names) — flagged in EXECUTION_PLAN.md Section 4,
  not resolved, not to be resolved autonomously.

## DO NOT RE-DERIVE
- Everything in EXECUTION_PLAN.md Section 2 (Settled Facts 1-11) and
  Section 9 (Strategic Decisions Already Made — asset class, growth-lever
  priority). These cost real effort to establish; build on them, don't
  re-argue them.
- The Three Laws and their two authorized overrides (advisor layer
  training on historical data; crossover breeding) — see
  AUTONOMOUS_TODO.md Decisions Made if you need the full rationale, but
  don't re-litigate whether they should exist.

## IMPORTANT NEW KNOWLEDGE
- See "What was learned" above — the cost-model defect and the post-tax
  metric gap are the two concrete, actionable findings from this pass.
- The project now has a formal three-tier session-continuity system:
  AUTONOMOUS_OPERATING_SYSTEM.txt (the protocol itself, immutable unless
  Het asks to revise it), EXECUTION_PLAN.md (the compressed operational
  map, derived from the three strategy documents), and this file (the
  literal handoff). Keep all three in sync going forward — if you change
  what Phase 0 means, update EXECUTION_PLAN.md; if you finish a Phase 0
  item, update state.json and this file, not the operating system doc.
