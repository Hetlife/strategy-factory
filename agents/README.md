# agents/ — the "team," and what it is actually allowed to do

Het asked for this explicitly ("make the team you think is necessary...
deliberately have different agents and their codes in it, represented in
subfolders") after being warned this isn't a Phase 0/1 priority per
EXECUTION_PLAN.md, and confirmed "build it anyway" via a direct choice.
This directory is that build. Recorded as a deliberate, informed override —
same category as the Law 1/Law 2 overrides in AUTONOMOUS_TODO.md, not a
silent scope expansion.

**The override is scoped narrowly: organization and read-only tooling, not
new financial risk.** Nothing in this directory computes a verdict, writes
`factory_state/ledger.json`, or changes `RULES`/`LADDER`/`COST_PER_SIDE`.
`factory.py` and `advisors.py` remain the only two files with write access
to state and the only source of truth for promotion/demotion/evolution
logic — everything here either wraps them read-only or adds a strictly
advisory, printed-only layer.

## The six agents

| Agent | File | What it actually is |
|---|---|---|
| Judge | `judge/judge.py` | Read-only re-derivation of `report()`'s per-contestant verdict math, for a plain "why did/didn't X get promoted" explanation. Does not decide anything `report()` hasn't already decided. |
| Researcher | `researcher/researcher.py` | Thin wrapper around `advisors.py`'s `train()` and `parameter_bank.json` reads. No new backtest logic. |
| Breeder | `breeder/breeder.py` | Renders the `lineage` field factory.py already records (via `spawn_neighbor`/`advisor_evolve`/`crossover`) as a readable family tree. Does not create contestants. |
| Risk Manager | `risk_manager/risk_manager.py` | **New logic**, but read-only/advisory only: sector concentration, aggregate real-money exposure (should be Rs 0 through Phase 0/1 — this is the one number worth watching), and a portfolio-wide correlated-drawdown flag that no single contestant's DEMOTE check can see. Wired into `factory.report()` as an additive printed section, after the ledger is already saved. |
| Reporter | `reporter/reporter.py` | **New logic**, plain-English translation of `report()`'s output (promotions, demotions, evolutions, births, best/worst performer) — for Het's stated preference for explanation over raw tables. No financial computation of its own. Wired into `factory.report()` the same way, last. |
| Healer | `healer/healer.py` | Runs `tools/health_check.py`'s deterministic repo-consistency checks (registry drift, state.json well-formedness, CLAUDE.md hash drift, bug_log/state.json contradictions) and prints plain findings. **Never fixes anything itself** — detection only, same as the others. See "Code over tokens" below for why this exists. |

## Code over tokens

Het's framing, 2026-08-25: "pass on work that can be done with code to
code" instead of a session re-deriving the same facts from scratch via
many tool calls every time. The concrete trigger was a real incident —
P0-3's `nifty_benchmark` sat merged in code but silently absent from the
live ledger for a full day, and the only reason it surfaced was Het
happening to ask "are the agents actually trading?" and a session manually
reading the raw ledger by hand.

`tools/health_check.py` is the response: a pure-Python script (no LLM
judgment needed to run it) that answers exactly that class of question —
is the ledger missing anything seed_registry() defines, does state.json
agree with itself, does CLAUDE.md's recorded hash match its real content,
does bug_log.md contradict what state.json says is resolved. `healer.py`
is the thin presentation layer over it. **Any session, before manually
re-deriving repo-consistency facts via a chain of Read/Bash/GitHub-API
calls, should run this first** — it's free, deterministic, and catches
the exact class of bug that cost a full day of silent drift last time.

This is wired into the daily report Routine's prompt (see
`.autonomous/het_directives.md`) so it runs automatically, at zero
additional session cost, as part of the existing schedule — not as a new
paid Routine. Extend `tools/health_check.py` with new checks whenever a
session finds itself manually re-deriving the same fact more than once;
that repetition is the signal a check belongs here instead.

## Why this shape

`factory.py`'s `report()` already produces everything these agents need
(`rows`, `evolved`, `born`, the saved `state` dict) — duplicating that
computation would be exactly the kind of curve-fit-risk drift the Three
Laws exist to prevent (two codepaths that could quietly diverge on what a
verdict actually is). So every agent either:

1. **Wraps** existing factory.py/advisors.py logic read-only (judge,
   researcher, breeder), or
2. **Adds** genuinely new but strictly advisory/printed logic that cannot
   affect a verdict, capital, or the ledger (risk_manager, reporter).

`factory.report()` calls `risk_manager.report()` and
`reporter.weekly_digest()` at the very end, after `save_state(state)` has
already run and after every verdict/evolution/breeding decision is final —
wrapped in a `try/except` so a bug in this newer, less-tested layer can
never break the actual tournament report. If you see that except branch
firing, that's a bug in `agents/`, not in the core engine.

## What NOT to do here

- Do not give any agent write access to `factory_state/ledger.json` —
  `save_state()` stays exclusive to `factory.py`.
- Do not let `risk_manager.py` or `reporter.py` influence a PROMOTE/DEMOTE
  verdict, even indirectly (e.g. don't wire their output back into
  `propose_evolutions()` or `attempt_breeding()`'s candidate selection).
- Do not add a sixth agent that touches broker/execution/API-key code,
  options/futures/margin, or real-money deployment — those stay hard
  guardrails per `CLAUDE.md`, this directory doesn't create an exception.
- Do not treat `aggregate_real_money_exposure()` returning nonzero as
  something to silence — it's a tripwire. If it ever fires, stop and
  confirm it was an explicit, fresh, in-session authorization before doing
  anything else.
