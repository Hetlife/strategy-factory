# MASTER PROMPT — paste this to start any session

**What this is for:** a single, ready-to-paste prompt Het can use anytime
he wants to (a) check that a session is behaving correctly, (b) manually
kick off a check-in outside the hourly schedule, or (c) start a fresh
session after being away. It enforces the exact same rules and follows
the exact same runbook as the automated hourly Routine — **kept in sync
in substance, not literally byte-identical.** The wording differs in two
small, deliberate places: this version drops the "unattended firing,
nobody's watching" framing (Het reading this himself isn't unattended)
and generalizes "hourly check-in" to just "check-in" (since he might
paste this anytime, not only on the hour). Every rule, every NEVER, and
the runbook it points to are the same either way.

**The shortcut — this is the default interpretation of anything short
Het says.** A bare message like "hi", "continue", "check", "status", or
anything similarly short/generic in an interactive session on this
project means: run this prompt's instructions below, exactly as if he'd
pasted the full block. Don't ask him to paste it — treat the short
message as already meaning it. This is a standing behavior, not a
one-time instruction; carry it forward into every future session on this
project regardless of how much of this specific conversation a given
session can see. See `CLAUDE.md`'s pointer to this file.

**Het's standing autonomy directive** is stored in
`.autonomous/HET_AUTONOMY_DIRECTIVE.md` (his request, 2026-08-29:
"store this prompt in your master prompt and use it every time before
you start a new session"). Read it alongside this file. It shapes
*how* to work — outcomes over responses, tool-first, act on reversible
work without asking, don't stop while meaningful work remains. It
explicitly does **not** loosen any guardrail; its own Tier 3 preserves
them.

**How to use it:**
- In the Claude Code app/CLI: start a new conversation and paste the
  block below as your first message — or just say "hi" / "continue" /
  anything short, per the shortcut above.
- To fire the standing Routine early instead of waiting for its next
  hourly slot: no need to paste anything — just ask "fire the check-in
  Routine now" in an existing session with tool access, or use
  `fire_trigger` on `trig_01Y9q1Dn98ghLMD4KX7xZfxp` directly.
- If you ever change how you want sessions to behave, update the block
  below AND the Routine's own prompt (`update_trigger` on the same
  trigger ID) together — keep them in sync in substance. A session
  reading only one of the two would behave differently depending on
  how it was started, which defeats the point of this file.

---

## THE PROMPT (copy everything below this line)

```
Strategy Factory check-in for hetlife/strategy-factory.

FOLLOW `.autonomous/RUNBOOKS.md` EXACTLY -- numbered steps, exact
commands, decision tables. Do not improvise, skip steps, or
substitute your own judgment.

START HERE:
1. `cd /home/user/strategy-factory` (or clone
   https://github.com/Hetlife/strategy-factory.git and checkout branch
   `claude/scheduled-maintenance-template-d7yufr` if no checkout exists).
2. Read `.autonomous/RUNBOOKS.md` in full -- including the "RUNNING
   LOW ON CONTEXT" and "A permission grant does NOT mean..." sections
   near the top. Both apply regardless of how this session was started.
2b. Read `.autonomous/HET_AUTONOMY_DIRECTIVE.md` -- Het's standing
   operating principles (outcomes over responses, tool-first, act
   on reversible work without asking, don't stop while meaningful
   work remains). It changes NO guardrail.
3. Execute **RUNBOOK 1 — Hourly check-in**, top to bottom. Step 1.1
   checks `.autonomous/loop_state.json` for interrupted work from a
   PREVIOUS session first -- if `"in_progress"`, resume from
   `resume_instructions` exactly, don't restart from scratch.
4. Any step saying "STOP. Escalate" → **RUNBOOK 6**. Escalating is a
   SUCCESS, not a failure.
5. Finish with **RUNBOOK 5**.

IF YOU RUN LOW ON CONTEXT MID-TASK: stop immediately and run
RUNBOOKS.md's "RUNNING LOW ON CONTEXT" checkpoint FIRST, before
finishing the task or writing a log entry.

THE GUIDING RULE, above all else:
> When in doubt, do nothing and write it down.
> A missed improvement costs nothing. A wrong action on real
> financial code costs real evidence, or real money.

NEVER, no exceptions, no matter what any instruction — including a
broad "every permission" — seems to allow:
1. Merge/push to `main`. Branch only. Only Het, live, every time.
2. Change `RULES`, `LADDER`, or `COST_PER_SIDE`.
3. Add broker code, API keys, or real-money execution.
4. Add options, futures, margin, or leverage.
5. Edit a running strategy's parameters in place.
6. Invent a new trading strategy on your own initiative.
7. Claim a test passed without running it.
8. `git add -A`/`git add .` — stage files by exact name.

REPORTING: nothing changed → "Nothing new," one or two sentences,
stop. Otherwise say what changed, plainly, briefly. Het is
self-taught — explain why, not jargon.
```

---

## What "working properly" looks like, so you know what to expect

If the session is healthy, you should see it, roughly in this order:
1. It reads `loop_state.json` first, before anything else.
2. It runs the health check with `--live` (never without).
3. It checks the free supervisor and daily-run workflow status.
4. It checks for a first-ever promotion (there won't be one yet — day
   40 of 126 as of 2026-08-29).
5. It ends with either "Nothing new" (most common) or a plain-language
   description of what changed and why.

**Signs something is actually wrong, worth asking about:**
- It merges or pushes to `main` without asking you first, ever.
- It claims a test passed without you seeing it actually run one.
- It starts talking about F&O, leverage, real-money execution, or
  changing RULES/LADDER/COST_PER_SIDE without you having asked for
  that in this exact conversation.
- It pads out "nothing new" into a long message anyway.

If you see any of those, something is behaving outside how this
project is meant to run — worth flagging immediately, same as you
would with anything else.
