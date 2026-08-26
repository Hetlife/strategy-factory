# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him.
5. .autonomous/bug_log.md — known OPEN/FIXED/CLOSED defects, check before
   assuming something is broken
6. AUTONOMOUS_LOG.md (tail -30, don't read the whole thing)
7. .autonomous/operator_profile.md — before writing anything Het will
   read: plain language, why not just what, hands-off on code
8. agents/README.md — the agents/ team + the "code over tokens" pattern
9. EXECUTION_PLAN.md — only if you need the phase/gate detail this file
   compresses away

## CURRENT STATE (as of 2026-08-26, commit `be5c8b1`)

**`main` has**: Phase 0 complete (P0-1..P0-4), the `agents/` team (judge,
researcher, breeder, risk_manager, reporter, healer), the LADDER raise to
`[0, 25k, 50k, 100k, 200k]`, the nifty_benchmark ledger-backfill fix,
`tools/health_check.py`, the dashboard "Office" tab + factor toggle, and
the paper-tier holding-cost decay (`PAPER_HOLDING_TAX_WEEKLY`). PRs #1-#4
all merged with Het's fresh explicit confirmation each time.

**ONE thing is on the branch, NOT yet merged**: the shared-graveyard
anti-repeat guard (`factory.graveyard()`/`already_failed()`, commit
`d1e4db4`). It changes live evolution behavior (skips an otherwise-valid
evolution round in the rare case of an exact repeat of an already-failed
setup) — needs Het's fresh explicit merge confirmation before it goes to
main, same pattern as every other behavior-changing change this session.
**This is the single most actionable item for whoever picks this up next
if Het hasn't already answered it.**

**Phase 1 = STANDING MODE** (EXECUTION_PLAN.md Section 4) is technically
still in force, but this session shipped several real feature additions
at Het's explicit, repeated request (agents/healer, dashboard Office tab,
holding-cost decay, shared graveyard) — each one confirmed via
AskUserQuestion before building, not assumed. This is a deliberate,
repeatedly-informed override pattern (same category as the Law 1/Law 2
overrides), not scope creep — but if a session finds itself wanting to
add something NEW beyond what's already been explicitly asked for, that's
where Phase 1 discipline should reassert itself. Build what's asked,
confirmed, and tested — don't invent new features on your own initiative.

**Two Routines exist**:
- `trig_01Y9q1Dn98ghLMD4KX7xZfxp` — daily report, 13:00 UTC, push-notified,
  detection/reporting only. Works reliably (it never needs to commit).
- `trig_01KoWHtWkQnLaW9WhHo3kumu` — nightly maintenance, 21:00 UTC (~2:30
  AM IST, timezone ASSUMED not confirmed — flag to Het if wrong), fires a
  fresh session, push-notified, deliberately detection-only for the same
  reason.
- `trig_013GUxs9AwHaRvb1o4eGJRGx` — the old 5-hourly autonomous dev-loop
  Routine — **stays DISABLED indefinitely.** Failed 5 confirmed times
  across 2 structurally different fixes. Het explicitly chose manual/
  interactive operation over continued debugging. Do NOT re-enable or
  re-fire without either a genuinely new diagnostic capability (real
  transcript visibility into what a Routine session does internally,
  which doesn't exist yet) or a fresh explicit ask from Het.

A live status Artifact exists for Het at
https://claude.ai/code/artifact/c8ef2e56-3280-4141-b6fd-bc14c91333c1 — it
was NOT updated this session (the dashboard's Office tab has mostly
superseded its purpose for real-time viewing), consider whether it's
still worth maintaining or should be retired in favor of the dashboard.

**Active cost awareness**: Het asked (2026-08-25) to be asked before any
new paid session/Routine is fired without him prompting it. He has since
explicitly asked for the nightly Routine himself, so that one's fine. The
underlying principle still holds: don't spin up new paid sessions on your
own initiative without asking, but normal work inside an already-running
interactive session is fine.

## WHAT WAS DONE THIS SESSION (2026-08-25 evening → 2026-08-26, chronological)
- Closed the autonomous-loop investigation: 5 confirmed failures, Het
  chose manual check-ins. `bug_log.md` entry marked CLOSED (accepted, not
  fixed), not FIXED.
- Found and fixed a real bug: `nifty_benchmark` had never actually been
  running live despite being merged, because `load_state()` only seeds a
  ledger that doesn't exist yet. General fix (backfills ANY missing
  `seed_registry()` key), not nifty_benchmark-specific. PR #2.
- Built `tools/health_check.py` + `agents/healer/healer.py` ("code over
  tokens" — Het's request to stop re-deriving repo-consistency facts by
  hand every session). Immediately caught 2 real issues (the
  nifty_benchmark gap, a stale `claude_md_sha1`), both fixed. Wired into
  the existing daily report Routine, zero new cost. PR #3.
- Built the dashboard "Office" tab (org-chart view of all 6 agents, live
  from GitHub) + a leaderboard factor-rating toggle. PR #4 (bundled with
  the item below).
- Built the paper-tier holding-cost decay (`PAPER_HOLDING_TAX_WEEKLY =
  0.13%/week`, ~6.5%/year, anchored to roughly India's risk-free rate).
  Reuses the existing drawdown-retirement pathway. PR #4.
- Built the shared graveyard (`factory.graveyard()`/`already_failed()`) —
  **on branch, not merged**, see above.
- Set up the nightly maintenance Routine (detection-only).
- Pushed back directly on "make the model learn as fast as possible" —
  declined to build anything that would fake evidence-accumulation speed,
  explained why (Law 1, the 12-month Phase 1 evidence window).

## WHAT WAS LEARNED
- **Every feature this session was preceded by an `AskUserQuestion` on the
  concrete design choice** (dashboard platform, notes-box scope, decay
  mechanism/rate, office-visual literalness) before building — this
  worked well and caught real scope mismatches early (e.g. "prompt area"
  turned out to mean a notes box, not a live AI chat). Keep doing this for
  anything with more than one reasonable design.
- **Test your own tests.** The shared-graveyard integration test initially
  gave a false "PASS" because `EVOLUTION_TOP_N` rank-filtering was
  masking the actual check being tested, not because the graveyard logic
  worked. Caught by adding a control case (same setup minus the graveyard
  entry, expecting a DIFFERENT outcome) and noticing it also produced
  nothing. Worth remembering as a general lesson: a test that always
  passes regardless of the thing you're testing isn't validating anything.
- `ledger.json` (registry + contestants) has always functionally been the
  "common library" every mechanism in this project reads from — several
  of Het's requests this session (healer, graveyard, dashboard) were
  really about making that existing shared state legible/visible rather
  than building new shared infrastructure from scratch. Worth remembering
  before assuming a "shared data" request needs a new data store.
- Streamlit + a local headless-browser check (not just `curl` for an HTTP
  200) is the right way to verify dashboard.py changes — a Streamlit app
  is a JS SPA, so a raw HTTP response tells you almost nothing about
  whether it actually rendered without exceptions.

## WHAT REMAINS
state.json `queue`, in rough priority order:
- **`shared-graveyard-anti-repeat`** (P1) — on branch (`d1e4db4`), needs
  Het's merge decision. Check `.autonomous/het_directives.md`'s NEEDS HET
  section first — he may have already answered by the time you read this.
- `P1-dashboard-auth` — blocked_on_human, needs Het with a real browser.
- `P1-advisor-training-real-run` — unblocked (PR #1 merged), no action
  needed unless Het wants it manually triggered before its monthly cron.
- `P3-anti-pattern-visibility-for-new-agents` — done_pending_merge, same
  item as shared-graveyard-anti-repeat above (duplicated at two priority
  levels intentionally, see state.json for why).
- Fund research (SEBI PMS/AIF/RIA) — early scoping done in a prior
  session, not committed to this repo (deliberately kept separate). SEBI
  RIA route specifically was flagged as worth researching further but
  never was. Check with Het before continuing — it may not still be a
  live priority.
- P2/P3 items — low-priority/gated per Phase 1's "don't add machinery"
  guidance where not already explicitly requested. See state.json.

## EXACT NEXT TASK
1. `git fetch` + check `state.json`/`het_directives.md`'s NEEDS HET
   section — this file is a snapshot, those are live.
2. If Het has answered the shared-graveyard merge question: act on it
   (merge via a new PR against main + `mcp__github__merge_pull_request`,
   or explicitly note he said hold).
3. If Het hasn't answered yet and you're a scheduled/unattended firing:
   do NOT merge on your own initiative — this needs his fresh explicit
   confirmation, no exceptions, regardless of how confident the testing
   looks.
4. Otherwise: standing-mode discipline applies. Watch for a real PROMOTE
   (first ever, flag prominently). Don't start new features beyond what's
   already been explicitly asked for and confirmed.
5. If a genuinely new request comes in from Het: same pattern as this
   session — clarify ambiguous scope via AskUserQuestion before building,
   test thoroughly (including a control case, see WHAT WAS LEARNED
   above), commit to the branch, ask before merging to main if it changes
   live financial/evolution behavior, don't ask if it's pure tooling/docs
   (like health_check.py was — that got merged without a separate
   merge-specific question because dashboard/tooling changes were
   pre-approved as low-risk in that batch's own AskUserQuestion).

## FILES TO OPEN
- `.autonomous/state.json`, `.autonomous/het_directives.md`,
  `.autonomous/bug_log.md` — the three living trackers.
- `agents/README.md` — the "code over tokens" pattern and what each agent
  actually does; read before assuming a new check needs a new agent
  rather than a new function in `tools/health_check.py`.
- `factory.py` only if there's an actual bug to fix or a Het-confirmed
  feature to build — not for unprompted feature work.

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt — already
  compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only.

## TEST COMMANDS
No committed test suite exists — all testing is ad hoc, in `/tmp`, against
synthetic monkeypatched price data (Yahoo Finance unreachable here).
Recreate a `synthetic_test.py`-style script as needed. For anything
touching `propose_evolutions()`/`attempt_breeding()`, write BOTH a
positive test (the mechanism does what's intended) AND a control/negative
test (the same setup minus the one variable, expecting a DIFFERENT
result) — see WHAT WAS LEARNED above for why this matters.

For `dashboard.py` changes: `streamlit run dashboard.py --server.headless
true --server.port <N>`, then verify with a headless browser
(`playwright`, pre-installed at `/opt/pw-browsers/chromium`) — check
`page.inner_text('body')` for exception/traceback text, don't just check
for an HTTP 200.

## EXPECTED RESULT
Nothing about a routine session should surprise Het when he checks in —
every behavior-changing addition this session was confirmed via
AskUserQuestion before being built, tested thoroughly (with controls) 
before being trusted, and asked about again before touching main. Keep
that discipline. A session that builds something Het didn't ask for, or
merges something without asking, is breaking the pattern that's worked
well so far.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite beyond what's already been explicitly
  requested and confirmed — kill-condition signal per EXECUTION_PLAN.md
  Section 5(f).
- You're about to fire a new paid session/Routine without Het having
  asked for it first.
- You're about to merge anything to main without a fresh, specific
  confirmation for THAT change (a prior "yes" on a different change
  doesn't carry over).
- You're about to build a feature Het hasn't actually asked for, even if
  it seems like a natural extension of something he did ask for.
- You're below ~20-30% of usable session context — stop, spend the
  remainder verifying and rewriting state.json/log/this file.

## OPERATOR AUTHORIZATION REQUIRED
- Merging the shared-graveyard anti-repeat guard to main (commit
  `d1e4db4`) — changes live evolution behavior.
- Confirming dashboard.py's private-repo auth (needs Het, real browser).
- Any future request implying pooled/outside capital — needs its own
  dedicated conversation (SEBI registration territory).
- Re-enabling or re-firing the disabled autonomous dev-loop Routine.

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts) and Section 9 (Strategic
  Decisions).
- The Three Laws and their authorized overrides — see state.json
  `decisions` for the full list with commit references.
- The autonomous-loop root-cause investigation — closed, Het chose manual
  operation, don't reopen without a genuinely new diagnostic capability.
- Why `graveyard()`/`already_failed()` are deliberately narrow (exact
  match only, never hypothesis-generating) — this is a Law 1 boundary
  that was reasoned through carefully, not an oversight to "improve" by
  making it fuzzier/smarter later without the same care.

## IMPORTANT NEW KNOWLEDGE
- `ledger.json` is the de facto "common library" every mechanism already
  shares — remember this before assuming a new shared-data request needs
  new infrastructure.
- `agents/README.md`'s "code over tokens" section is the standing
  instruction for when to add a `tools/health_check.py` check vs. when to
  just answer a question by hand once.
- Two working Routines (daily report, nightly maintenance) share the same
  reliability pattern: detection/reporting only, never trying to
  fix-and-commit autonomously. The disabled dev-loop Routine is the
  cautionary example of why that boundary exists.
