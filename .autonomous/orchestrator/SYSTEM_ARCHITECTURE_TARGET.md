# System Architecture — Target State

The orchestrator directive's Section 22 envisions a higher-reasoning
model overseeing a fleet of cheaper agents, a formal token budget, and a
verifier layer. This file states what of that is actually appropriate
to build **during Phase 1 standing mode**, and what is deliberately
deferred, so `GAP_ANALYSIS.md` isn't answering an unstated target.

## What the target state actually is, for THIS phase

Phase 1's own rule (`EXECUTION_PLAN.md` §4, `CLAUDE.md`) is: run the
schedule, accumulate real evidence over the ~12-month window, **do not
add new structural machinery**. So the target architecture for Phase 1
is not "build the orchestrator" — it's "make the existing free
automation and the existing session-based check-ins as reliable and
cheap as they can be without adding a new always-on system." Concretely:

1. **Automation layer** (unchanged from current): `factory.yml`,
   `supervisor.yml`, `advisor_training.yml` — free, deterministic,
   already running. Target = stays exactly this, no new workflow adds
   judgment where a script already suffices.
2. **Session layer** (the one thing that can improve): RUNBOOK 9 is the
   standing cycle. Target = every session (hourly Routine or Het pasting
   the master prompt) runs it consistently, checkpoints via
   `loop_state.json`, and routes itself to the cheapest model that can
   do the task honestly (see `AGENT_MODEL_ROUTING.yaml`).
3. **Verification layer** (new, small, already piloted this session):
   for any change that touches financial logic (the promotion gate,
   cost model, RULES), an adversarial read-only subagent review before
   the change is trusted — not a permanent service, a repeatable
   pattern invoked when the stakes warrant it. See
   `VERIFICATION_PROTOCOL.md`.
4. **Multi-agent orchestrator runtime (Section 22's literal ask):
   explicitly NOT part of the Phase 1 target.** A persistent
   orchestrator process is new structural machinery, is exactly the
   shape of thing that already failed 5 times (`P0-5`), and Phase 1 has
   no task that needs 24/7 multi-agent coordination — `update()`/
   `report()` are already free cron jobs. Revisit only if Phase 2
   (post-first-honest-verdict, `MASTER_PLAN.md` STEP 5) introduces work
   that genuinely can't be a scheduled script.

## What "done" looks like for Phase 1's target

- Every RUNBOOK 9 cycle ends in one of its four legitimate states
  (nothing found / fixed in-bounds / queued for Het / context low) —
  no fifth state, no profit-chasing drift.
- A session that starts on a cheap model can tell, from `state.json` +
  `AGENT_MODEL_ROUTING.yaml`, which of its pending queue items it can
  safely do itself vs. which need a stronger model or Het's judgment.
- Any RULES/LADDER/COST_PER_SIDE change goes through the same pattern
  Q5/Q6 did: written analysis → Het's fresh explicit choice → adversarial
  review → merge only with a fresh in-session "yes".
