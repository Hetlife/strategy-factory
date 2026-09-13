# Recovery Spec

This formalizes a mechanism that is **already in production**, not a
new one. `loop_state.json` has been used for real crash/resume at least
twice (2026-08-29 session-end checkpoint, 2026-09-05 orchestrator-audit
checkpoint that this very session resumed from). This document exists
so the contract is explicit rather than only implicit in the file's own
`_doc` field.

## The contract

**File:** `.autonomous/loop_state.json`

**States:**
- `"idle"` — no interrupted work. A new session/firing starts fresh from
  `state.json` + `next_session.md`.
- `"in_progress"` — a previous session was cut off mid-task. The current
  session MUST resume from `resume_instructions` exactly — not restart
  from scratch, not second-guess what's already committed.

**When to write it:**
1. At the START of any multi-step task, BEFORE the risky/irreversible
   part — commit and push immediately so a crash mid-task still leaves
   a usable resume point.
2. Again when the task finishes cleanly (reset to `idle`) OR when
   stopping safely for another reason (context running low, waiting on
   Het) — with `status` reflecting which.

**What `resume_instructions` must contain**, learned from real use:
- What the task is and who/what authorized it.
- Which specific files/commits already exist vs. still pending — a
  resuming session should be able to `git log` and cross-check rather
  than trust the description blindly.
- Any backgrounded work (a subagent launched, a `workflow_dispatch` not
  yet checked) — otherwise a resuming session duplicates it.
- Explicit boundaries: what NOT to do (e.g. "no merge", "no RULES
  change") so a resume can't accidentally exceed the original
  authorization.

## Verified failure modes this already handles

- Context running out mid-task (RUNBOOKS.md's "RUNNING LOW ON CONTEXT"
  section triggers the checkpoint before anything else).
- A session ending between "wrote the file" and "logged it" — the
  `git log`-vs-`resume_instructions` cross-check in RUNBOOK 9 Step 9.1
  catches this (this session's own resume did exactly this check).

## What this spec does NOT cover

- Recovery for a workflow run failure inside GitHub Actions itself —
  that's `supervisor.yml`'s job (staleness detection), not
  `loop_state.json`'s.
- Recovery for a subagent that fails mid-review (rate limit, org spend
  cap) — the parent session simply re-launches it; no special state
  file is needed since subagent results are stateless reports, not
  multi-step committed work.
