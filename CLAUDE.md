# Strategy Factory — repo constitution

Condensed from the project's founding docs (never committed to this repo
as separate files — this is the canonical, self-contained version).
Read this first, every session. For live state (queue, decisions, recent
history) read `.autonomous/state.json` FIRST — it's cheap and structured.

**`GOALS.md`** — the north star: what we're actually trying to prove,
realistic timeline for when we'll know (not a profit forecast — an
honest one doesn't exist yet), and scenario math explicitly labeled as
contingent, not predicted. Read it to stay oriented on the point of the
work, distinct from `EXECUTION_PLAN.md`'s rules/gates/mechanics.

**As of 2026-08-24 the project also has `EXECUTION_PLAN.md`** — a
condensed strategic reference (settled facts, phase gates, kill
conditions, growth-lever priority, guardrails) derived from
`mission_document.txt`/`pivot_document.txt`/`understanding.txt`. Read it
before doing any substantive work — `state.json.current_phase` tells you
which phase applies, and `EXECUTION_PLAN.md` tells you what that phase
means. The project is currently in **Phase 0**: four gating deliverables
(size-aware cost model, post-tax expectancy metric, Nifty benchmark
contestant, committed falsification criteria) must ship before any other
feature work resumes. Only read `AUTONOMOUS_TODO.md` in full when doing
substantive work; it's prose and costs more tokens per read.

**`AUTONOMOUS_OPERATING_SYSTEM.txt`** is the full session-protocol spec
(source-of-truth hierarchy, task sizing, code-change protocol, session
log/state formats, kill-switch discipline). This file (CLAUDE.md) is the
fast-path summary of it. `.autonomous/next_session.md` is the literal,
spoon-fed handoff for whichever session runs next — read it after
`state.json`, before doing any work, and rewrite it before ending your
own session so the one after you doesn't need this conversation's
history.

**`.autonomous/bug_log.md`** — append-only defect log (OPEN/FIXED), distinct
from `AUTONOMOUS_LOG.md`'s terse action-by-action record. Check it before
assuming something is broken (it may already be a known, fixed issue) and
add to it whenever you find or fix a real bug in this project's own logic.

**`.autonomous/operator_profile.md`** — how Het wants any session
(autonomous or interactive) to communicate with him: plain language, WHY
not just WHAT, hands-off on code but wants real understanding, honest
answers over comfortable ones. Read it before any exchange that will
reach him directly (this matters far less for the unattended autonomous
loop, which mostly just does the work — it matters most for interactive
sessions and for anything written for him to read later, like commit
messages or a status summary).

## What this is

An automated, self-evolving tournament of trading strategies for Indian
equities (NSE), built by Het (SevaaConnect Solutions Pvt Ltd). Goal: prove
whether a real trading edge exists, at near-zero cost, before risking
capital. An evidence machine, not a money machine. See
`.autonomous/state.json` → `queue` for current work,
`AUTONOMOUS_TODO.md` → `Current Objective`/`Decisions Made` for full
narrative.

## The Three Laws (binding, never violate without explicit fresh authorization)

1. Hypotheses are written before testing — never mined from data.
2. Live strategies are never mutated — only replaced via bred children
   that start over at rung 0.
3. Capital is earned through the ladder, never granted.

**Two standing, explicitly authorized exceptions** — see
`AUTONOMOUS_TODO.md` → Decisions Made for full rationale, do not re-derive
or re-litigate them:
- The advisor layer (`advisors.py`) trains on historical price data —
  Law 1 override, authorized.
- `report()`'s evolution step replaces paper-tier (rung 0) stragglers —
  Law 2 override, authorized, but mechanically still only ever creates a
  new registry key and never touches a real-money-rung contestant.

## Architecture (current, post-advisor-layer)

- `factory.py` — the core engine. `update()` runs daily (P&L, positions).
  `report()` runs weekly (Sharpe/drawdown, PROMOTE/DEMOTE/retire verdicts,
  advisor-informed evolution). State: `factory_state/ledger.json`
  (registry + contestants), never hand-edited.
- `advisors.py` — monthly training script. Backtests a mechanism-bounded
  parameter grid through the same `sig_*` functions `factory.py` runs
  live, scores with 3 heuristics (sharpe/robustness/cost-efficiency),
  writes `factory_state/parameter_bank.json`.
- `dashboard.py` — Streamlit read-only view, fetches from GitHub raw URLs.
  Never a write path.
- `.github/workflows/factory.yml` — daily update + Sunday report, commits
  `ledger.json` back to `main`. `.github/workflows/advisor_training.yml` —
  monthly, commits `parameter_bank.json`.
- `factory_state/advisor_state.json` — self-tuning `trust_weight` (how
  much evolution blends toward the advisor's pick).

## Hard rules — never do these without explicit, separate, in-session human authorization

- Never edit `factory_state/ledger.json` by hand.
- Never change `RULES` (promotion thresholds), `LADDER` (capital amounts),
  or `COST_PER_SIDE` — financial risk parameters, not code-quality knobs.
- Never mutate an existing `registry` dict entry that has contestant
  history — new ideas are new registry keys.
- Never add a strategy whose parameters were chosen by grid-searching
  historical data without a stated real-world mechanism first (outside
  the already-authorized advisor layer).
- Never add options/futures/margin/leverage logic.
- Never add or modify broker/execution/API-key code.
- Never enable real-money execution or deploy capital.
- Never merge a PR, push directly to `main`, or force-push — without a
  **fresh, explicit, in-session** confirmation. A prior session's "yes"
  does not carry forward to a new session.
- Never make the repository public.

## Known environment quirks (don't re-derive these — save the tokens)

- Yahoo Finance is unreachable from Claude Code sandbox environments in
  this project's testing so far (network policy). Test against synthetic/
  monkeypatched price data and say so explicitly; don't claim a real-data
  test that didn't happen. GitHub Actions runners DO have real network
  access — real validation happens there, not in an interactive session.
- This sandbox's outbound proxy transparently authenticates GitHub
  requests (`GH_TOKEN=proxy-injected` in env) — a `curl`/`requests` fetch
  succeeding from inside a session proves nothing about what a real
  anonymous visitor would see. Don't re-attempt to test `dashboard.py`'s
  private-repo auth this way; see the open queue item in
  `.autonomous/state.json` for what's actually still needed.
- All work happens on branch `claude/scheduled-maintenance-template-d7yufr`
  (PR #1). If it's not there, check that branch/PR before assuming no
  work has happened — don't assume `main` is current.

## Efficient session protocol

1. Read `.autonomous/state.json` (small, structured — cheap).
2. Run `git log --oneline -3` and `git status` (cheap sanity check, not a
   substitute for state.json — just confirms it isn't stale).
3. Only read this file's full architecture section if state.json's
   `claude_md_hash` doesn't match what you'd expect — normally you
   already just read it as step 1 of a session, so this is naturally
   satisfied.
4. Only read `AUTONOMOUS_TODO.md` in full when you need the narrative
   rationale for a decision, or when about to do substantive work that
   needs full context. Don't read it reflexively every firing — its
   compact facts already live in `.autonomous/state.json`.
5. Do the work. Update `.autonomous/state.json` (structured, cheap).
   Append ONE line to `AUTONOMOUS_LOG.md` (terse, append-only). Only
   touch `AUTONOMOUS_TODO.md`'s prose when there's new narrative-worthy
   rationale (a new decision, a new architecture note) — not for routine
   "did task X" bookkeeping, which belongs in the log instead.
