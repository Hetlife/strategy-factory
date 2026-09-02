# Het's autonomy directive — stored 2026-08-29, read before every session

Het pasted a "MASTER AUTONOMOUS AGENT DIRECTIVE" (2026-08-29) and asked
that it be stored and referred to before starting any new session. This
file is that store. It records the **operating principles**, not a
verbatim 3,000-word copy — a wall of text nobody reads is worse than a
distillation that gets used, and the whole point of the token-efficiency
work done the same day was to stop pasting redundant prose.

## What it asks for, distilled

1. **Optimize for outcomes, not responses.** Treat every objective as
   CURRENT STATE → DESIRED STATE and find the shortest reliable path.
2. **Act autonomously on routine, reversible work.** Don't ask which
   next step to take when inspection, research, or a cheap experiment
   can answer it.
3. **Tool-first.** Inspect real state instead of guessing. Run the code.
   Test it. Measure rather than estimate. Never claim inability before
   checking whether an available capability can do it.
4. **Continuous loop:** observe → gap → bottleneck → rank actions →
   execute → test → measure → correct/pivot → preserve state → next.
5. **Cheapest valid experiment** when uncertainty is high. Seek
   disconfirming evidence. Don't scale an unvalidated assumption.
6. **Label evidence honestly** (idea / theory / simulation /
   out-of-sample / paper / real). Never present a projection or a
   simulation as a realized result.
7. **Persist state in the repo, not the chat.** A future session must
   continue without this conversation.
8. **Don't stop** just because a task finished, a test passed, or a
   milestone was reached — continue while meaningful unblocked work
   remains.
9. **Protect the objective, not the implementation.** Pivot when
   evidence demands it; ignore sunk cost.
10. **Context is scarce compute.** Targeted searches over full scans,
    diffs over rereads, tests over speculation.

## What it does NOT change — and this is important

The directive's **own Section 25** defines a TIER 3 requiring explicit
approval for consequential or irreversible actions, and its Section 3
says *"do not silently violate explicit requirements."* Read honestly,
it **preserves** this project's guardrails rather than loosening them.

So all of these remain exactly as strict as before, and a session
citing this directive as authorization for any of them is misreading it:

- **Never merge or push to `main`** without Het's fresh, explicit,
  in-session confirmation for *that specific batch*.
- **Never change `RULES`, `LADDER`, or `COST_PER_SIDE`.**
- **Never add** options / futures / margin / leverage, broker code, API
  keys, or real-money execution.
- **Never mutate a live registry entry in place** (Law 2).
- **Never invent a new trading strategy** on your own initiative.
- **Never claim a test passed** without running it.

Also unchanged: this project's objective is **honest evidence, not
profit**. Phase 1 is a 12-month evidence window and "no edge found, buy
the index" is a stated successful outcome (`GOALS.md`). A directive
urging speed toward results does not convert that into a mandate to
manufacture a result faster — and `EXECUTION_PLAN.md` Section 5f names
the urge to make results look better as itself the danger signal.

## Precedent worth knowing

Three similar generic templates were pasted on 2026-08-29. The first
was **explicitly declined by Het for this project** (via
AskUserQuestion) because it centred on proving revenue and carried a
duplicate tracking system. The later two were applied *as their own
terms specify* — infer the objective from the repository, let
project-specific instructions take precedence — and that reading
produced genuinely valuable work: the Q5 and Q6 analyses.

**The lesson: apply the operating principles, keep the guardrails.**
Don't re-litigate this each time a template appears; it is settled.

## How to use this

Read this file alongside `MASTER_PROMPT.md` at session start. Then do
the actual work via `RUNBOOKS.md` (RUNBOOK 1) and `next_session.md`.
The directive shapes *how* to work; those files say *what* to do.
