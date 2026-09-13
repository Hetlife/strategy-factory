# Master Execution Plan (orchestrator-directive planning pass)

This is a planning artifact, not a replacement for `MASTER_PLAN.md`
(which owns the forward research sequence: Q4/Q5/Q6, Het's promotion-bar
decision, Phase 2 trigger). This file is scoped to what the orchestrator
directive itself asked for: how the *session/tooling* layer should run,
given the gaps in `GAP_ANALYSIS.md`.

## Sequence (in order, each step gated on the one before it)

1. **Read-only audit** — done, 2026-09-13 (`SYSTEM_ARCHITECTURE_CURRENT.md`).
2. **Adversarial review of the one piece of financial logic that had
   never been independently checked** — the Q5/Q6 promotion gate
   (`factory.promotion_check`). Launched this session; result recorded
   in `AUTONOMOUS_LOG.md` and, if any defect is CONFIRMED, filed in
   `bug_log.md` and queued in `state.json` (not silently fixed — a
   change to `promotion_check` touches the same territory as
   RULES/LADDER and gets the same fresh-authorization treatment).
3. **Write the eleven planning documents** — done, this pass, on the
   feature branch, not merged.
4. **Do NOT build the multi-agent orchestrator runtime.** Recorded as a
   deliberate non-action with reasoning in `GAP_ANALYSIS.md` and
   `SYSTEM_ARCHITECTURE_TARGET.md`.
5. **Resume the standing RUNBOOK 9 cycle** as the default session
   behavior going forward — this planning pass is a one-time detour,
   not a new permanent step every session repeats.
6. **Commit to the branch, log, reset `loop_state.json` to idle.** No
   merge — merges always need a fresh, in-session, explicit "yes" from
   Het, and this is docs/tooling, not something urgent enough to ask
   for one unprompted.

## What happens next session (so a cheap model can pick this up cold)

- Read `state.json` → `loop_state.json` (should read `idle`) →
  `next_session.md`.
- Default behavior is RUNBOOK 9, same as before this directive arrived.
  This directory (`.autonomous/orchestrator/`) is reference material —
  read it only if asked about the orchestrator directive itself, or when
  deciding which model a task needs (`AGENT_MODEL_ROUTING.yaml`).
- If Het gives a decision on either open NEEDS-HET item (the ~6-week
  promotion-clock slip acceptance, or the 15 never-traded contestants'
  thresholds — both in `het_directives.md`), that's real work; this
  planning pass is not.

## Explicit non-goals (so nobody "completes" these by accident)

- Do not stand up a persistent orchestrator process.
- Do not build a token-metering system.
- Do not treat "audit everything" as license to touch RULES, LADDER,
  COST_PER_SIDE, or merge to `main` without the usual fresh confirmation.
- Do not invent new queue items just to make the task graph look busier
  than the real backlog — `TASK_GRAPH.json` is built from `state.json`,
  not from imagination.
