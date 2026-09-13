# Gap Analysis — Current vs. Target (2026-09-13)

| Area | Current | Target (Phase 1) | Gap | Action |
|---|---|---|---|---|
| Daily/weekly automation | Running, free, verified green through 2026-09-11 (`factory.yml`), 2026-09-13 (`supervisor.yml`) | Same | None | No action — this is already correct. |
| Promotion gate correctness | Q5/Q6 fix merged 2026-09-02; never independently adversarially reviewed until this pass | Reviewed once by an adversarial subagent before being trusted for a real verdict | Was open | Closed this session — see `promotion_gate_review.md` (scratchpad) and the finding recorded in `AUTONOMOUS_LOG.md`. |
| Verification layer | `health_check.py --live` only (deterministic, structural) | + a repeatable adversarial-review pattern for financial-logic changes | Was open | Closed — documented in `VERIFICATION_PROTOCOL.md`. |
| Token/model routing | Ad hoc: Het manually switches `/model`; no written guidance on which task needs which model | A short table mapping task type → cheapest sufficient model | Open | `AGENT_MODEL_ROUTING.yaml` (this pass) closes the documentation gap. Does not add automation — Het still chooses the model. |
| Token budget/cost accounting | None | Some | Open, deliberately not fully closed | `TOKEN_BUDGET.yaml` records honestly that no metering system exists and that building one is out of scope for Phase 1 (it would be new structural machinery with no task driving it — Het's own standing rule is "ask before anything costing," not "meter everything"). |
| Multi-agent orchestrator runtime | Does not exist; a similar 5-hourly Routine failed 5x and was abandoned | Section 22 of the directive asks for one | Large | **Not closed, deliberately.** See `SYSTEM_ARCHITECTURE_TARGET.md` and `MASTER_EXECUTION_PLAN.md` — building this now would repeat `P0-5`'s failure mode with no new reason to expect a different outcome, and Phase 1 doesn't need it (crons already cover the recurring work). Revisit at Phase 2. |
| OpenClaw/LucyOS integration | Does not exist in this repo (researched only for Het's personal PC, delivered to him directly, out of this repo's scope) | Not requested by anything in `CLAUDE.md`/`EXECUTION_PLAN.md` | None (target correctly excludes it) | No action inside this repo. |
| Recovery/crash-resume | `loop_state.json`, proven in real use at least twice | Formal spec of the same contract | Documentation gap only | `RECOVERY_SPEC.md` (this pass) writes down the contract already in production; no behavior change. |
| Task tracking | `state.json.queue` (23 items, structured, real) | A task graph showing dependencies, not just a flat list | Small | `TASK_GRAPH.json` (this pass) — built FROM the real queue, not invented; explicitly does not add new tasks that don't already have a stated reason to exist. |

## Bottom line

Most of the "gap" the directive implicitly assumes was already closed
by this project's existing discipline (free crons, `loop_state.json`,
`state.json`, RUNBOOK 9). The two real, substantive gaps this pass
closes are the missing adversarial review of the promotion gate and the
missing written model-routing guidance. The one gap deliberately left
open — a persistent multi-agent orchestrator — is a considered decision
grounded in this project's own documented failure history, not an
oversight.
