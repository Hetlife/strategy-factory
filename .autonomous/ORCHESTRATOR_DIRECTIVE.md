# Orchestrator Directive — stored 2026-09-05, distilled

Het pasted a "STRATEGY FACTORY — HIGH-REASONING ORCHESTRATOR DIRECTIVE"
(25 sections, fable-5-1 session, 2026-09-05). Per this project's own
convention (see `HET_AUTONOMY_DIRECTIVE.md`) this file stores the
**operating principles**, not a verbatim copy — a wall of text nobody
re-reads is worse than a distillation that gets used.

## What it asks for (Section 23, its own first action)

A READ-ONLY system audit, then eleven planning deliverables under
`.autonomous/orchestrator/`: current-state architecture, target-state
architecture, a gap analysis, a master execution plan, a task graph, a
model-routing table, an authority matrix, milestone rules, a token
budget, a recovery spec, and a verification protocol. Explicitly: no
large architecture change and no code change to `factory.py` until the
plan itself is reviewed. That instruction was followed literally —
these are planning/reference documents, not new runtime code.

## Adopted, with two resolved tensions

**ADOPTED** as consistent with `CLAUDE.md` and Phase 1 standing mode —
unlike the earlier generic "MASTER AUTONOMOUS EXECUTION PROMPT" template
(2026-08-29), which was declined because it conflicted with this
project's Hard Rules and was not in Het's own voice. This directive
does neither of those things.

1. **Eleven separate files vs. this project's anti-duplication
   discipline.** CLAUDE.md's whole design (see its own opening
   paragraph) is one canonical file per concern, cross-referenced, never
   restated. Resolution: write each file as instructed, but where its
   content is already owned by an existing file, keep it a **thin
   pointer** (a paragraph + a link) instead of re-deriving it. Concretely:
   `MILESTONE_RULES.yaml` points at `EXECUTION_PLAN.md` §4-5 rather than
   re-typing the kill conditions; `AUTHORITY_MATRIX.yaml` points at
   `CLAUDE.md`'s Hard Rules rather than re-stating them as a second,
   driftable copy.
2. **Section 22 (a persistent multi-agent orchestrator runtime) vs. the
   documented prior failure.** `state.json` queue item `P0-5` records
   that an earlier 5-hourly autonomous dev-loop Routine failed 5
   confirmed times and was abandoned by Het's own decision
   (`abandoned_by_het_decision`). Building a new always-on multi-agent
   runtime would repeat exactly that shape of failure without a stated
   reason the outcome would differ this time. Resolution: `GAP_ANALYSIS.md`
   and `MASTER_EXECUTION_PLAN.md` record this explicitly and do NOT
   recommend building one now. RUNBOOK 9's Scan→Plan→Execute→Log cycle
   (single session, deterministic tooling first, checkpointed via
   `loop_state.json`) already covers the same ground with a proven
   crash/resume mechanism and no repeat of the P0-5 failure mode.

## What this directive does NOT change

Same as every other standing instruction in this repo: it does not
loosen CLAUDE.md's Hard Rules, does not authorize a merge to `main`, does
not authorize inventing a new trading strategy, and does not authorize
skipping fresh in-session confirmation for anything the Hard Rules gate.
A session citing "Section 23 says audit everything" as license to change
`RULES`/`LADDER`/`COST_PER_SIDE` or merge is misreading it, the same way
`HET_AUTONOMY_DIRECTIVE.md`'s own Tier 3 preserves every guardrail.

## Honest audit findings that shaped the plan (2026-09-05/2026-09-13)

- No OpenClaw/LucyOS integration exists in this repo. It was researched
  and documented for Het's own PC setup (scratchpad files, sent to him
  directly) but nothing about it lives in `strategy-factory` and nothing
  should — this project's automation is GitHub Actions, not a local
  agent runtime.
- No token-accounting system exists. Model choice today is a manual
  practice (cheap model for mechanical RUNBOOK 9 cycles, a stronger model
  reserved for genuine research/planning), not a metered budget. See
  `TOKEN_BUDGET.yaml` for what's real vs. aspirational here.
- No separate "verifier layer" existed before this pass. The closest
  real thing is `health_check.py --live` (deterministic, free, runs in
  CI) plus, new as of this pass, an ad-hoc adversarial subagent review
  pattern for financial-logic changes — see `VERIFICATION_PROTOCOL.md`.
