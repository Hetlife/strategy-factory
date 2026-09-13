# Verification Protocol

Two layers exist. Neither is a persistent service — both are patterns a
session invokes, not infrastructure that runs unattended.

## Layer 1 — deterministic, free, structural: `health_check.py --live`

Runs the same structural checks every time (registry/ledger drift, agent
responsiveness, real_money_exposure=0 on every agent). Free, fast, no
judgment involved. **Run this first, always**, before spending any model
reasoning on "is something broken." A clean run rules out an entire
category of problems for zero cost.

## Layer 2 — adversarial subagent review, for financial-logic changes only

**When to use it:** before trusting a change to anything that decides
money movement — the promotion gate, the cost model, RULES-adjacent
logic — and did not already go through this once. Not for every commit;
docs/tooling changes don't need it.

**How (the pattern used this session, reusable verbatim):**
1. Launch a `general-purpose` Agent, explicitly READ-ONLY (no edits, no
   commits, writes only to a scratchpad report file).
2. Give it the exact file list and function names to review, plus the
   real-world stakes in one sentence ("a false promotion risks real
   money on noise").
3. Ask specific, falsifiable questions (not "is this good code?") —
   e.g. "can this return True when it shouldn't, and what's the
   concrete failing input?"
4. Require it to distinguish CONFIRMED (built a real failing input) from
   speculative concerns, and to give one final severity verdict.
5. Treat the report as an input to a decision, not a decision itself —
   a CONFIRMED CRITICAL/HIGH finding gets queued in `state.json` +
   `bug_log.md` and, if it implies a RULES-adjacent code change, still
   needs Het's fresh authorization before shipping, same as any other
   change to that territory.

**First real run:** launched 2026-09-13 against `factory.promotion_check`
/ `excess_return_stats` / `multiplicity_sharpe_floor` (the Q5/Q6 gate,
merged 2026-09-02, never independently reviewed until now). Result
recorded in `AUTONOMOUS_LOG.md` and, if applicable, `bug_log.md`.

## What this protocol deliberately does not become

- Not a CI gate — there's no test suite and building one is a separate,
  larger decision (would need Het's sign-off, is not in scope here).
- Not a standing service — no scheduled "verifier agent" runs on its
  own. Each invocation is a session decision, logged like any other.
- Not a substitute for Het's authorization on Hard-Rule-gated changes —
  a CONFIRMED-sound review is evidence for a decision, not the decision.
