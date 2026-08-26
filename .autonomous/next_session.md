# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer,
   and the new "Standing autonomy rule" section: free work needs no ask,
   anything close to costing does — does NOT loosen the merge/push hard
   rules, which still need Het's fresh confirmation every time)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him.
5. .autonomous/hr_log.md — hires made via agents/hr/hr.py (0 so far)
6. .autonomous/it_guy_protocol.md — read this specifically if
   supervisor.yml has failed recently, before doing anything else
7. .autonomous/bug_log.md — known OPEN/FIXED/CLOSED defects
8. AUTONOMOUS_LOG.md (tail -40, don't read the whole thing)
9. .autonomous/operator_profile.md — before writing anything Het will
   read: plain language, why not just what, hands-off on code
10. agents/README.md — the agents/ team, hiring protocol, "code over
    tokens" pattern

## CURRENT STATE (as of 2026-08-26 ~12:28 UTC, commit `d06880a`)

**Het is away for a few days as of this writing (his own message).**
Branch and main are fully in sync — no open merge backlog. Everything
built this session is live on `main`, and was re-verified working AFTER
that last message (see "REAL BUG FOUND AND FIXED" below — don't assume
"merged" means "actually works," check).

**Since the "away for days" handoff was first written, also shipped**:
- Fixed a real bug in `supervisor.yml` — it never installed
  `pandas`/`numpy`, so every run crashed before checking anything
  (caught by actually triggering it via `workflow_dispatch`, not by
  trusting the earlier local-only test, which had those pre-installed).
  Verified fixed via a second real run — conclusion `success`.
- `tools/build_trading_floor_state.py` — auto-generates the Trading
  Floor artifact's data snapshot from real repo state (agents
  auto-discovered from `agents/*/*.py`, leaderboard from real
  `ledger.json`, activity from `AUTONOMOUS_LOG.md`, open questions from
  `het_directives.md`'s NEEDS HET section) instead of hand-typing it
  into an inline script each time. **Use this, don't hand-write the
  state JSON again** — see its docstring for usage.
- `dashboard.py`'s Arena tab: static "Paper Bankroll / Rs 100,000"
  metric replaced with a live "Top Performer" metric (name + % return).
- CLAUDE.md: "Outsource to free tooling first" rule (formalizes the
  pattern already running — prefer a free script/workflow over paid
  reasoning for mechanical work) and a note that Het now calls the
  project "the company" in conversation — explicitly NOT a scope change.
- Het also asked for a "75%-confidence" rule (act autonomously above
  75% confidence on a judgment call, otherwise queue it for him) and a
  two-way "notebook" he can reply into. Written into CLAUDE.md as its
  own section ("Confidence threshold for judgment calls") — a THIRD
  axis alongside cost and risk, scoped to already-delegated,
  non-hard-rule territory only (does NOT relax the Hard Rules section).
  The "notebook" is the Trading Floor Artifact's note bowl +
  `het_directives.md`'s NEEDS HET section — explicitly not a new thing
  to build; `dashboard.py`'s local notes box was flagged as NOT the
  right channel (it's local-only, doesn't reach a session elsewhere).

**What's live on main**: Phase 0 complete, the `agents/` team (now
SEVEN: judge, researcher, breeder, risk_manager, reporter, healer, hr),
per-agent `workspace.md` files, `tools/health_check.py`, the dashboard
Office tab (7 desk cards) + heartbeat banner + factor toggle, paper-tier
holding-cost decay, the shared graveyard anti-repeat guard, the market
log ("mother file"), free open monsoon rainfall data (research-only,
NOT wired to the live signal — see factory.py's `sig_monsoon` comment),
crude oil (Brent) input-cost hypotheses for cement/steel, the free
15-minute GitHub Actions supervisor (`tools/supervisor_check.py` +
`.github/workflows/supervisor.yml`), the IT-guy protocol (event-driven
bug-fixing, piggybacks on the two existing Routines, never merges
without Het), and the new CLAUDE.md standing autonomy rule.

**A published Artifact exists for Het** — "Trading Floor",
https://claude.ai/code/artifact/6af2bce8-b4a5-4b08-b60a-916c239e8a65 —
a mobile-first pixel-office view he can open on his phone with no setup.
Has the `artifact` capability declared (he can write notes that persist
via `claude.use('artifact').publish()`). **This session cannot get
live-notified when he writes a note** (no watch support for remote
sessions yet) — if a future session wants to check, use
`Artifact({action: "read", url: "..."})` and look at the `notes` array
in the embedded `page-state` JSON. Republish (same `file_path`, pass
`url` to update in place) whenever the underlying data materially
changes — it's a snapshot, not live-fetched (Artifact CSP blocks
client-side fetch to GitHub anyway).

**Two Routines + one free workflow are the standing operation while
Het is away** (confirmed with him directly, 2026-08-26 — he explicitly
declined a more active/expensive background loop):
- `trig_01Y9q1Dn98ghLMD4KX7xZfxp` — daily report, 13:00 UTC.
- `trig_01KoWHtWkQnLaW9WhHo3kumu` — nightly maintenance, 21:00 UTC
  (~2:30 AM IST, timezone assumed not confirmed).
- Both now ALSO check `supervisor.yml`'s recent runs and follow
  `.autonomous/it_guy_protocol.md` if it found a real error — diagnose,
  fix+test ON THE BRANCH, never main, surface for Het's confirmation.
- `.github/workflows/supervisor.yml` — every 15 min, free, GitHub
  Actions only, no Claude session. Only fails on a real "error"-level
  `health_check` finding or >3 days ledger staleness — not the routine
  self-healing warnings.
- `trig_013GUxs9AwHaRvb1o4eGJRGx` — the old 5-hourly autonomous dev-loop
  Routine — **stays DISABLED indefinitely.** Failed 5 confirmed times.
  Do not re-enable without a genuinely new diagnostic capability or a
  fresh ask from Het.

**Standing instruction while Het is away**: no new proactive feature
work, no merges to main, without him. The Routines/supervisor/IT-guy
protocol keep the lights on for free or near-free; anything that needs
a real decision queues in `het_directives.md`'s NEEDS HET section
instead of being guessed at.

## WHAT WAS DONE THIS SESSION (2026-08-26, chronological, high level)
- Verified real trading/learning activity, fixed a real bug
  (`nifty_benchmark` silently missing from the live ledger).
- Built `tools/health_check.py` + `agents/healer/healer.py` ("code over
  tokens").
- Built the dashboard Office tab, heartbeat banner, and a re-rank toggle.
- Built the paper-tier holding-cost decay and the shared graveyard
  anti-repeat guard.
- Sourced free open monsoon rainfall data (research-only, not live) and
  added crude-oil input-cost hypotheses (a real, direct mechanism) after
  explicitly declining a weaker gold hypothesis Het offered to add anyway
  — he chose to skip it.
- Built the market log ("mother file") — pure record-keeping, never read
  by any signal.
- Built the free 15-min GitHub Actions supervisor and the IT-guy
  protocol, after directly flagging the cost tradeoff and the history of
  the disabled dev-loop Routine — Het chose the free/event-driven design
  both times.
- Built the HR agent (`agents/hr/hr.py`) and per-agent `workspace.md`
  files, after clarifying scope via AskUserQuestion first (team-role
  tooling only, never trading strategies; 10 hires pre-authorized).
- Built and iterated the "Trading Floor" Artifact through three
  redesigns: pocket-office → uptime-hero + animated door → fullscreen
  walk-in office view with working/sleeping zones.
- Recorded a new CLAUDE.md "Standing autonomy rule" (free work needs no
  ask, anything close to costing does) at Het's explicit request,
  written to be clear it doesn't loosen the merge/push hard rules.
- Merged everything (PRs #6, #7, #8, #9) with Het's fresh confirmation
  each time — final one specifically because he was about to be away.

## WHAT WAS LEARNED
- **Every feature this session was preceded by an `AskUserQuestion` on
  ambiguous design/scope/cost before building** — this keeps working
  well, including for genuinely high-stakes asks (the HR agent's scope
  was clarified before writing a line of code, since "hire more agents"
  could easily have meant something that touches Law 1). Keep doing this.
- **Cost vs. risk are different axes** — Het's "do free things, ask
  about cost" rule is about money; it does not and should not be read
  as loosening the separate, unconditional "never merge/push main
  without fresh confirmation" rule. Keep them explicitly distinct in any
  future session's reasoning, don't let a broad permission grant blur
  into the narrower hard rules.
- **When a session can't build the ideal solution (true event-driven
  wake-on-CI-failure), say so plainly and build the honest fallback**
  (piggybacking on existing scheduled Routines) rather than either
  overpromising or silently doing nothing. The IT-guy protocol doc
  states its own ~12h worst-case latency directly.
- Streamlit + a local headless-browser check (not just `curl` for HTTP
  200) is the right way to verify `dashboard.py` changes. The same
  applies to the Artifact — test in a real headless browser before
  publishing, `window.claude` won't exist there so the note-save
  fallback path gets exercised for free.
- For the Artifact's two-way notes: capture `document.documentElement.
  outerHTML` and split HEAD/TAIL around the `page-state` script tag
  **at the very start of the script**, before any render()/DOM mutation
  — this avoids the "don't serialize a live DOM" pitfall the
  artifact-capabilities skill warns about, since the textarea's typed
  value never gets read via outerHTML (it's injected into the state
  object directly instead).

## WHAT REMAINS
- **Dashboard hosting decision** — Streamlit Community Cloud offered
  (free, but the resulting link is public with no built-in access
  control on the free tier). Het hasn't decided yet; not urgent, the
  Artifact already works as a phone-checkable view meanwhile.
- `P1-dashboard-auth` — blocked_on_human, needs Het with a real browser
  in an incognito tab.
- Fund research (SEBI PMS/AIF/RIA) — parked, not committed to this repo,
  check with Het before reviving.
- HR agent: 0/10 hires used. Don't manufacture a hire just to use the
  allowance — only scaffold a new helper when a session judges there's
  a real, observed gap (same bar that produced healer.py).
- A "news" data source for the input_cost family — still not found
  (nothing free/simple/reliable enough yet). Keep flagging rather than
  force a low-quality one in.
- `supervisor.yml`'s cron (`*/15 * * * *`) hadn't fired on its own yet
  as of this file's last edit (only ~10 min since the fix was merged —
  too early to tell anything from that). The code itself is confirmed
  working (manual `workflow_dispatch` succeeded twice). If a future
  session checks and it's STILL never fired on schedule after a few
  hours, that's worth actually investigating, not just noting again.

## EXACT NEXT TASK
1. `git fetch` + check `state.json`/`het_directives.md`'s NEEDS HET
   section — this file is a snapshot, those are live.
2. Read `.autonomous/hr_log.md` and `.autonomous/it_guy_protocol.md` if
   you haven't already (short files, cheap).
3. If this is a Routine firing (daily report or nightly maintenance):
   follow that Routine's own prompt exactly, including the new
   supervisor.yml check + IT-guy protocol step.
4. If this is an interactive session with Het: normal operation — read
   what he's asking for, clarify ambiguous scope/cost/risk via
   AskUserQuestion before building anything non-trivial, test thoroughly,
   commit to the branch, ask before merging to main every time.
5. If this is an unattended/scheduled session and nothing looks broken:
   don't invent work. Phase 1 standing-mode discipline still applies —
   watch for a first-ever real PROMOTE (flag prominently if it happens),
   don't start new features on your own initiative.

## FILES TO OPEN
- `.autonomous/state.json`, `.autonomous/het_directives.md`,
  `.autonomous/bug_log.md`, `.autonomous/hr_log.md` — living trackers.
- `agents/README.md` — the team, hiring protocol, "code over tokens."
- `.autonomous/it_guy_protocol.md` — only if the supervisor found
  something.
- `factory.py` only if there's an actual bug to fix or a Het-confirmed
  feature to build — not for unprompted feature work.

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt —
  already compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only.

## TEST COMMANDS
No committed test suite exists — all testing is ad hoc, in `/tmp`,
against synthetic monkeypatched price data (Yahoo Finance unreachable
here). For anything touching `propose_evolutions()`/`attempt_breeding()`,
write BOTH a positive test AND a control/negative test (same setup minus
the one variable, expecting a DIFFERENT result).

For `dashboard.py`/Artifact changes: `streamlit run dashboard.py
--server.headless true --server.port <N>`, then verify with a headless
browser (`playwright`, pre-installed at `/opt/pw-browsers/chromium`) —
check `page.inner_text('body')` for exception/traceback text, don't just
check for an HTTP 200.

Quick health check before trusting anything: `python3
tools/health_check.py` and `python3 tools/supervisor_check.py` against
real live data (fetch fresh from main, don't trust a stale local copy).

## EXPECTED RESULT
Nothing about a routine or unattended session should surprise Het when
he's back. Every behavior-changing addition gets confirmed via
AskUserQuestion before being built, tested thoroughly before being
trusted, and asked about again before touching main — including during
his absence. A session that builds something he didn't ask for, or
merges something without asking, breaks the pattern that's worked well
so far.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite beyond what's already been explicitly
  requested and confirmed.
- You're about to fire a new paid session/Routine, or run this session
  itself on an expensive active loop, without Het having asked for it —
  he explicitly declined this on 2026-08-26.
- You're about to merge anything to main without a fresh, specific
  confirmation for THAT change.
- You're about to build a feature Het hasn't actually asked for.
- You're about to scaffold an HR-agent hire without a real observed gap,
  or scaffold anything that reads like trading-strategy territory
  (agents/hr/hr.py's guardrail will refuse the latter, but don't rely on
  the code catching a judgment call the session should have made first).
- You're below ~20-30% of usable session context — stop, spend the
  remainder verifying and rewriting state.json/log/this file.

## OPERATOR AUTHORIZATION REQUIRED
- Any merge to main, every time, no exceptions carried forward.
- Confirming dashboard.py's private-repo auth (needs Het, real browser).
- Deciding on Streamlit Community Cloud hosting (free but public link).
- Any future request implying pooled/outside capital.
- Re-enabling or re-firing the disabled autonomous dev-loop Routine.
- HR agent hire #11 onward (0/10 used as of this writing).
- Any request to speed up evidence-accumulation or otherwise touch how
  Phase 1's 12-month window works — "earn real money" is the real goal,
  restated by Het 2026-08-26, but he was told directly it changes
  nothing about the path there.

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts) and Section 9 (Strategic
  Decisions).
- The Three Laws and their authorized overrides — see state.json
  `decisions` for the full list with commit references.
- The autonomous-loop root-cause investigation — closed, Het chose
  manual operation.
- Why `graveyard()`/`already_failed()` are deliberately narrow (exact
  match only, never hypothesis-generating).
- Why the monsoon data is research-only and not wired to `sig_monsoon`'s
  live path (the source data ends in 2017 — dropping it live would make
  the signal forward-fill a 9-year-stale reading forever).
- Why the HR agent is scoped to team-role tooling only, never trading
  strategies (confirmed with Het via AskUserQuestion, not assumed).
- Why the IT-guy protocol piggybacks on existing Routines instead of a
  new schedule (the earlier autonomous fix-and-commit loop failed 5
  times; a new standing schedule risks the same failure mode plus real
  recurring cost Het didn't ask for).

## IMPORTANT NEW KNOWLEDGE
- `ledger.json` is the de facto "common library" every mechanism already
  shares.
- `agents/README.md`'s "code over tokens" section is the standing
  instruction for when to add a check/agent vs. answer by hand once.
- The Trading Floor Artifact's HEAD/TAIL-split republish pattern (see
  WHAT WAS LEARNED above) is reusable for any future artifact that needs
  two-way state with Claude.
- Sandbox network policy blocks data.gov.in/IMD/most .gov domains
  directly, but GitHub raw content is reachable — useful for sourcing
  free datasets when the official source is blocked.
