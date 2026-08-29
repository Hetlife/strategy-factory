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
means. **Phase 0 cleared 2026-08-24** (all four gating deliverables
shipped: size-aware cost model, post-tax expectancy metric, Nifty
benchmark contestant, committed falsification criteria). The project is
now in **Phase 1 — standing mode**: run the daily/weekly schedule, let
real evidence accumulate over the ~12-month window, and do NOT add new
structural machinery. `state.json.current_phase` is the live source of
truth if this line ever disagrees with it. Only read
`AUTONOMOUS_TODO.md` in full when doing substantive work; it's prose and
costs more tokens per read.

**`.autonomous/RUNBOOKS.md`** — **the fully mechanical version: exact
commands, exact expected output, explicit decision tables, and "STOP and
escalate" wherever real judgment is needed.** Written for a session
running on a smaller/cheaper model, but any session can follow it. If
you are unsure what to do at any point, this file, not improvisation,
is the answer. Its guiding rule: *when in doubt, do nothing and write it
down* — a missed improvement costs nothing, a wrong action on financial
code costs real evidence.

**`.autonomous/SESSION_PLAYBOOK.md`** — **the step-by-step procedure for
running a session, start to finish.** Numbered steps, exact commands,
the decision rules for what to work on, the testing standard, and a
"things that look broken but aren't" table that will save you from
re-investigating settled non-issues. Unlike `next_session.md` (a
snapshot that goes stale), this is a stable procedure. **If you read
only one file after this one, read that.**

**`PROJECT_STUDY.md`** — **the full narrative history: everything done
so far, why, and what it means, organized by theme (Phase 0 buildout,
the autonomous-loop failure and how it was resolved, monitoring bugs
fixed, dashboard evolution, the pattern for adding a new contestant,
every declined/bounded request and the reasoning, real bugs found).
Read this when you need the *why* behind a decision or precedent for a
request that rhymes with something asked before — not for routine
task execution, which is what `SESSION_PLAYBOOK.md`/`RUNBOOKS.md` are
for.** Distinct from `AUTONOMOUS_TODO.md` (shorter, only the most
load-bearing decisions) and `AUTONOMOUS_LOG.md` (terse, one line per
action, the primary source this file was built from).

**`AUTONOMOUS_OPERATING_SYSTEM.txt`** is the full session-protocol spec
(source-of-truth hierarchy, task sizing, code-change protocol, session
log/state formats, kill-switch discipline) — 800 lines, the exhaustive
version of what `SESSION_PLAYBOOK.md` covers practically. Reach for it
only when the playbook doesn't answer something. This file (CLAUDE.md)
is the fast-path summary. `.autonomous/next_session.md` is the literal,
spoon-fed handoff for whichever session runs next — read it after
`state.json`, before doing any work, and rewrite it before ending your
own session so the one after you doesn't need this conversation's
history.

**`.autonomous/bug_log.md`** — append-only defect log (OPEN/FIXED), distinct
from `AUTONOMOUS_LOG.md`'s terse action-by-action record. Check it before
assuming something is broken (it may already be a known, fixed issue) and
add to it whenever you find or fix a real bug in this project's own logic.

**`.autonomous/loop_state.json`** — the hourly check-in Routine's
crash/resume file (Het, 2026-08-26/27). Read it FIRST if this session is a
Routine firing: `status:"in_progress"` means a previous firing got cut off
mid-task, and you resume exactly from `resume_instructions`, never restart
from scratch. Written+pushed at the START of any multi-step task (before
the risky part), updated again on finish or safe stop. Not relevant to a
one-off interactive session unless you're specifically continuing a
Routine's interrupted work.

**`.autonomous/het_directives.md`** — append-only log of Het's own
instructions/requests over time (summarized intent, never a verbatim
conversation transcript — same reasoning as `operator_profile.md`'s "What
NOT to do"), with a standing "NEEDS HET" section for anything blocked on
him. Read it alongside `next_session.md`; carry its NEEDS HET section into
whatever you report back to him.

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

## Standing autonomy rule (Het, 2026-08-26)

"Do the free things whichever you want, just ask me if something even
close to costing comes, otherwise do as you please." This governs
**cost**, not **risk** — it's a separate axis from the Hard rules above,
which stay unconditional regardless of this grant (a merge to main
costs nothing in money but is still never done without a fresh,
in-session "yes" from Het, every time — see e.g. 2026-08-24's identical
"give you every permission" grant, guardrails unchanged then for the
same reason). In practice: free/reversible work (code changes on the
branch, new GitHub Actions workflows, docs, read-only research, an
Artifact) — proceed without asking. Anything that spends money, a paid
Claude session/Routine firing, or is genuinely ambiguous about whether
it might — ask first, don't guess in Het's favor.

## Outsource to free tooling first (Het, 2026-08-26)

"Make sure you outsource all the work you want to free sources if you
have access to them, and use your API and brain on improving and
overseeing everything." Formalizes a pattern already in place before he
said it — `tools/health_check.py`, `supervisor.yml`, `factory.yml`,
`advisor_training.yml` all run as free, deterministic GitHub Actions
code, not Claude reasoning, precisely because the checks they do don't
need judgment. Before reaching for a paid session/tool call to do
something mechanical (a repeated check, a scheduled task, a fixed
transformation), ask: could this be a free script/workflow instead?
Reserve actual reasoning (planning, diagnosing an ambiguous bug,
judging whether a hypothesis has a real mechanism, deciding what a
finding means) for what genuinely needs it — that's the "brain" this
rule means to protect, not spend on work code can already do.

Het now calls this project "the company" in conversation — noted, no
objection, but this is a naming preference, not a scope change: still a
personal paper-trading research program, not a registered legal entity.
The SEBI/fund distinction from 2026-08-24 stands exactly as before ("we
are making a private fund" was corrected then, not revisited since) —
if "company" language ever seems to imply pooling outside money or
operating as a real firm, that still needs its own dedicated
conversation, not an assumption from the label.

## Confidence threshold for judgment calls (Het, 2026-08-26)

"If you're more than 75% sure just do it, otherwise [queue] the task,
keep a notebook in the dashboard I can see and reply to your question."
A THIRD axis alongside cost (money) and risk (the Hard rules) — this one
is about **certainty**. Applies only inside territory a session already
has standing authority over (a bug diagnosis, a tooling/code-quality
call, which of several reasonable implementations to pick) — it does
NOT touch the Hard rules section above, which stays confirmation-
required regardless of how confident a session feels; 90%-confident on
a financial-parameter change is still not authorization, because
confidence isn't the same thing as authorization. Where it's genuinely
below ~75% (a real judgment call, not just "I'd rather not decide"),
queue it instead of guessing -- and, per Het's own follow-up (2026-08-26,
via a note on his hosted dashboard, see below), don't just idle waiting
on that one answer: keep working on other already-pending, already-
authorized tasks while the uncertain one sits queued.

**The "notebook" is the Trading Floor Artifact's note bowl + this
file's own NEEDS HET section — not a new thing to build.** The Artifact
(https://claude.ai/code/artifact/6af2bce8-b4a5-4b08-b60a-916c239e8a65)
already lets Het write back (`artifact` capability, persists in the
page's own state, readable via `Artifact({action:"read", url:...})`),
and shows Claude's open questions pulled live from
`het_directives.md`'s NEEDS HET section via
`tools/build_trading_floor_state.py`. `dashboard.py` (Streamlit) has a
separate, LOCAL-ONLY notes box (`.autonomous/dashboard_notes.md`) that
only works when Het runs the dashboard himself on his own machine — it
does not reach a session running elsewhere, so don't treat it as the
two-way channel; the Artifact is.

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
