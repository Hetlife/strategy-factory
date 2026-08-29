# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer)
2. **`.autonomous/RUNBOOKS.md`** — fully mechanical, exact commands,
   decision tables, "STOP and escalate" wherever judgment is needed.
   **If you are a smaller/cheaper model, or unsure at any point, this
   is the answer — not improvisation.** Start at RUNBOOK 1.
3. **`.autonomous/SESSION_PLAYBOOK.md`** — the same flow but assuming
   more judgment. Read this if you're operating with more latitude.
4. .autonomous/state.json (structured queue, decisions, test status)
5. This file (the snapshot of where things stand right now)
6. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him.
7. .autonomous/loop_state.json — the hourly Routine's crash/resume file.
   Read FIRST if this session is a Routine firing: `status:"in_progress"`
   means a previous firing got cut off mid-task, resume exactly from
   `resume_instructions`, never restart from scratch.
8. .autonomous/bug_log.md — known OPEN/FIXED/CLOSED defects
9. AUTONOMOUS_LOG.md (tail -40, don't read the whole thing)
10. .autonomous/operator_profile.md — before writing anything Het will
    read: plain language, why not just what, hands-off on code
11. **`PROJECT_STUDY.md`** (new, 2026-08-29) — the full narrative
    history: why things are the way they are, every declined/bounded
    request with its reasoning, real bugs found. Read when you need
    *precedent or understanding*, not for routine task execution.

## CURRENT STATE (as of 2026-08-29, branch commit `588789c`)

**Phase 1, day 40 of the 126-day minimum evaluation window** (oldest
contestants — verified live, not estimated). All contestants still
rung 0 (paper), Rs 0 real money anywhere, zero promotions ever. No
breeding/evolution yet — both mechanisms need `days_on_rung >= 126`,
correctly not triggered this early, not a bug.

**Contestant count, and why two numbers are both right:**
`seed_registry()` defines **27**; `ledger.json` on main has **26**
live. The difference is `mom_nifty100_lb90`, merged to main in code
but not yet backfilled into the ledger. `load_state()` backfills it on
the next `factory.py update()` run. This gap is exactly what
`health_check.py --live` reports as its self-healing registry-drift
warning, and it's why the new contestant does not yet appear on the
dashboard (which reads the ledger, not the code).

**`factory.yml` cron: Mon-Fri 12:45 UTC, Sun 04:30 UTC.** The Sunday
run does BOTH `update()` and the weekly `report()`. If you are reading
this after Sunday 2026-08-30 ~04:30 UTC, that run should have
backfilled `mom_nifty100_lb90` and produced a weekly report — **verify
that actually happened** rather than assuming it did.

**Branch is 7 commits ahead of main**, all docs/tooling, no trading
logic, no `RULES`/`LADDER`/`COST_PER_SIDE`:
`f08890d` (merge records), `0f877b9` (fix: malformed commit field in
state.json), `c6e2bd9` (log), `856c439` (PROJECT_STUDY.md + RUNBOOK
7/8 + permission-grant section), `56abf31` (log), `e357ae8` (dashboard
verification log), `588789c` (study-file correction). Het was offered
the merge and had not answered as of session end — **ask fresh, don't
assume either way.**

## WHAT WAS LEARNED (2026-08-29 session)

- **A merge to main does not make a new contestant visible.** The code
  change and the ledger are separate; only a scheduled `update()` run
  bridges them. Verified end-to-end by actually rendering the dashboard
  headlessly, not by assuming.
- **Verify unfetchable claims via GitHub Actions instead of leaving
  them as human TODOs.** The Nifty 100 ticker basket was built from
  training knowledge (sandbox blocks NSE/Wikipedia/smallcase), then
  actually checked by a manual-dispatch diagnostic on a runner with
  real network access — which found 2 genuinely dead tickers
  (`TATAMOTORS.NS`, `LTIM.NS`, real HTTP 404s, likely a corporate-action
  symbol change). Removed rather than guessing replacements. This is
  now RUNBOOK 8.
- **A new workflow file must exist on `main` before it can be
  dispatched against any ref** — including its own branch. Confirmed
  again via a real 404.
- **"You have every permission" does not relax any guardrail.** Het
  said this again (framed around reaching "consistent large profit").
  Declined the implied authorization to touch RULES/LADDER/
  COST_PER_SIDE or self-merge, citing CLAUDE.md's own precedent and
  GOALS.md's actual goal. This is now an explicit section at the top of
  RUNBOOKS.md so a smaller model recognizes the pattern mechanically.
- **`pkill -f "streamlit run dashboard.py"` matches its own shell** and
  kills the command mid-execution (exit 144, silently losing later
  steps in the same invocation). If you background streamlit for a
  dashboard test, verify afterward that anything you chained after the
  kill actually ran.

## WHAT REMAINS

Nothing structural. Phase 1 standing mode: run the schedule, let the
evidence clock run, don't add machinery. Open items are all either
blocked on Het, permanently gated, or passive watches — see
state.json's queue. The genuinely valuable next event is **the
calendar**, not a commit.

## EXACT NEXT TASK

Run **RUNBOOK 1** (hourly check-in). If it comes back clean and
nothing changed, say "Nothing new" in one or two sentences and stop —
do not manufacture work. Two things specifically worth confirming on
the next run after Sunday 2026-08-30 04:30 UTC:
1. Did `mom_nifty100_lb90` actually land in `ledger.json` on main?
   (`health_check.py --live` should go fully clean when it does.)
2. Did the Sunday weekly `report()` run and commit? It's the first
   report since the new contestant merged.

## FILES TO OPEN
- `.autonomous/RUNBOOKS.md` — the mechanical procedures (start here)
- `.autonomous/state.json` — queue and decisions
- `PROJECT_STUDY.md` — why things are the way they are
- `factory.py` — only if making a real code change (see RUNBOOK 4/7)

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt —
  already compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only.

## TEST COMMANDS
- `python3 tools/health_check.py --live` — always use `--live`
  (avoids the stale-local-checkout false positive; this bug class has
  bitten twice).
- Synthetic regression pattern: copy `factory_state/` + `factory.py`
  into an isolated scratch dir, monkeypatch `fetch_prices()` with
  synthetic data (inject shock days if testing event_drift-family
  changes), run 40 `update()` cycles + `report()`, assert no crash and
  check new/changed entries behave correctly. Exact snippet in
  RUNBOOK 4 Step 4.3.
- Dashboard changes: `streamlit run dashboard.py`, then verify via a
  real headless-browser screenshot (Playwright, pre-installed at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) — don't just
  check for import errors.
- For any GitHub Actions workflow change: `workflow_dispatch` it for
  real and read the actual job logs (`mcp__github__get_job_logs`,
  `return_content: true`) — `conclusion: "success"` only means it
  didn't crash, not that the result was good news.

## EXPECTED RESULT
Phase 1 standing mode continues. Nothing should meaningfully change
session to session except accumulated ledger history, real registry-
parameter refinements grounded in real data, and genuine tooling
fixes. A session wanting to accelerate the evidence clock itself, or
build toward AI-controlled capital allocation, is violating this
project's own stated discipline — stop and flag it, don't build it.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite beyond what's already confirmed.
- You're about to merge anything to main without a fresh, specific
  confirmation for THAT batch of commits.
- You're about to build toward AI-controlled real capital allocation —
  declined explicitly, twice, needs its own dedicated conversation.
- You're about to add options/futures/margin/leverage — declined
  2026-08-29, logged, needs its own conversation.
- You're about to mutate an existing live registry entry's parameters
  in place instead of adding a new one — Law 2, corrupts accumulated
  evidence.
- You're below ~20-30% of usable session context — stop, spend the
  remainder verifying and rewriting state.json/log/this file.

## OPERATOR AUTHORIZATION REQUIRED
- Any merge to main, every time, no exceptions carried forward, no
  matter how broad a permission grant sounds.
- Confirming dashboard.py's private-repo raw-URL auth (needs Het, real
  browser) — separate from the public-visibility question already answered.
- Any request implying pooled/outside capital, or AI-controlled capital
  allocation.
- Options/futures/leverage of any kind.
- Deciding whether to replace cloud automation with local-only (Het is
  planning local deployment — LOCAL_SETUP.md deliberately does NOT set
  up a competing local cron, see its Section 6).
- The correct current NSE symbols for Tata Motors and LTIMindtree, if
  he knows them — both were removed from `UNIVERSE["nifty100"]` after
  real 404s; re-add only after verifying the same real way (RUNBOOK 8).

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts) and Section 9 (Strategic
  Decisions).
- The Three Laws and their authorized overrides — see state.json
  `decisions` for the full list with commit references.
- Why the event_drift recalibration added new entries instead of
  editing the originals (Law 2) — settled.
- Why "make it trade/learn faster" keeps getting the same answer
  (evidence clock runs on calendar days, not compute) — settled
  reasoning, re-explain fresh each time it comes up, don't silently
  ignore a new instance of the ask.
- The platform's 1-hour Routine minimum and the workflow_dispatch
  main-branch-first requirement — both confirmed via real API errors.
- That the sandbox cannot reach Yahoo Finance, nseindia.com,
  en.wikipedia.org, or smallcase.com — all confirmed by real attempts.
  Use a GitHub Actions diagnostic instead (RUNBOOK 8).
- That `curl https://api.github.com/...` returns **403** ("GitHub access
  is not enabled for this session"). The `mcp__github__*` tools are the
  only path to GitHub data — don't try to build a cheaper checker on
  curl, it cannot work.
- That `mcp__github__actions_list` **ignores `per_page`** and returns the
  full run list with full commit messages, so each workflow-status check
  costs thousands of tokens. Call it once per workflow per check-in.
  `tools/supervisor_check.py --live` answers the staleness half for free
  but cannot see a run that failed *today* — it complements the MCP
  check, it does not replace it.

## IMPORTANT KNOWLEDGE
- The hourly loop is proven reliable (unlike the old 5h dev-loop, which
  stays permanently disabled after 5 confirmed failures).
- Real advisor training has run against real data — `parameter_bank.json`
  exists on main.
- All 8 agents verified active against real data — if one seems broken
  later, that's a regression worth investigating, not an assumption.
- `report()`'s output includes a non-fatal `[warn] agents/ advisory
  layer failed ... No module named 'agents'` when run from an isolated
  scratch dir that doesn't have `agents/` copied in. That's a testing
  artifact, not a real failure.
