# The "IT guy" protocol

Het, 2026-08-26: an agent that fixes bugs the supervisor finds, gated on
his own confirmation before anything touches main. Deliberately NOT a
standing daemon or a new paid Routine -- see the history below for why.

## Why this isn't a session firing on its own schedule

An earlier attempt at exactly this shape of thing -- a session that
would autonomously fix things and commit, firing every 5 hours -- failed
5 confirmed times (real activity, zero commits) and Het chose manual
check-ins over continuing to debug it (`.autonomous/bug_log.md`, the
disabled `trig_013GUxs9AwHaRvb1o4eGJRGx` Routine). A new standing
schedule would risk the same failure mode and, separately, costs real
money on a fixed cadence regardless of whether anything's actually
broken -- which is exactly what Het declined when asked about the
supervisor's own cadence.

Instead: `.github/workflows/supervisor.yml` already checks every 15 min
for free (no Claude session). This protocol piggybacks on the two
EXISTING daily/nightly Routines (already running, already paid for) --
they check the supervisor's recent run history as part of their normal
check-in, and only act as the IT guy if it's actually found something.

**Known limitation, stated plainly**: this means a real problem can sit
for up to ~12 hours before an IT-guy pass looks at it (the gap between
the two existing Routine firings), not instantly. True "wake the moment
something breaks" isn't available with current tooling. If Het wants
faster response than that, the honest tradeoff is a session on a more
frequent fixed schedule -- real, recurring cost, which he already
declined for the supervisor's own checks. Don't silently build around
this limitation; say so if it matters for a given incident.

## The actual procedure

Any session (Routine-fired or interactive) that notices the supervisor
workflow has failed recently should:

1. Check `supervisor.yml`'s recent runs (`mcp__github__actions_list`,
   `list_workflow_runs`, `resource_id: "supervisor.yml"`). A `failure`
   conclusion means `tools/supervisor_check.py` hit an ERROR-level
   finding -- not the routine self-healing warnings it already ignores.
2. Read that run's log (`get_job_logs` / `get_workflow_run_logs_url`) to
   see exactly which finding failed it.
3. Diagnose the real root cause -- same rigor as any other bug in this
   project, not a guess. If it can't be confidently diagnosed, say
   exactly what's unclear and stop there rather than force a
   speculative fix (same discipline as the GitHub-PR CI-red rules this
   session already follows).
4. Build and test the fix on `claude/scheduled-maintenance-template-d7yufr`
   (the standing branch) -- never main, never a force-push, never
   skipping a test to make something pass. Before finalizing, run
   `agents.master_trader.master_trader.second_opinion_on_fix(description,
   files_touched)` -- a cheap keyword-based second check for the most
   obvious guardrail violations (touching `ledger.json` directly,
   changing `RULES`/`LADDER`/`COST_PER_SIDE` values). Any warning it
   returns goes into the report alongside the fix -- it's a flag, not a
   veto; the session still decides.
5. Commit and push the fix to the branch. Add it to
   `.autonomous/het_directives.md`'s NEEDS HET section and the day's
   report: what broke, what the fix does, why it's believed correct --
   waiting on Het's fresh, explicit confirmation before it goes anywhere
   near main. Same pattern as every other change this session, no
   exceptions for this agent specifically.
6. Never merge, never open a PR expecting auto-merge, never treat "the
   supervisor flagged it" as itself a form of permission -- the
   supervisor is pure code with no judgment; it can detect, not approve.
