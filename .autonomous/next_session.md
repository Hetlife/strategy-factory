# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer)
2. **`.autonomous/RUNBOOKS.md`** — fully mechanical, exact commands,
   decision tables, "STOP and escalate" wherever judgment is needed.
   **If you are a smaller/cheaper model, or unsure at any point, this
   is the answer — not improvisation.** Read the "RUNNING LOW ON
   CONTEXT" section near the top even if you don't need it yet — know
   where it is before you need it. Start the actual work at RUNBOOK 1.
3. **`.autonomous/SESSION_PLAYBOOK.md`** — the same flow but assuming
   more judgment. Read this if you're operating with more latitude.
4. .autonomous/state.json (structured queue, decisions, test status)
5. This file (the snapshot of where things stand right now)
6. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him.
7. **`.autonomous/loop_state.json` — READ THIS BEFORE ANYTHING ELSE.**
   This session ended with `status: "in_progress"` on purpose (context
   limit approaching, not a crash) — see its `resume_instructions` for
   exactly what was mid-flight. Do that first, don't restart from
   scratch, don't re-verify what it says was already tested.
8. .autonomous/bug_log.md — known OPEN/FIXED/CLOSED defects
9. AUTONOMOUS_LOG.md (tail -40, don't read the whole thing)
10. .autonomous/operator_profile.md — before writing anything Het will
    read: plain language, why not just what, hands-off on code
11. **`PROJECT_STUDY.md`** — the full narrative history: why things are
    the way they are, every declined/bounded request with its
    reasoning, real bugs found. Read for *precedent or understanding*,
    not for routine task execution.

## CURRENT STATE (as of 2026-08-29, branch commit `66ae914`)

**Phase 1, day 40 of the 126-day minimum evaluation window** (oldest
contestants, verified live). All contestants still rung 0 (paper),
Rs 0 real money anywhere, zero promotions ever. No breeding/evolution
yet — both need `days_on_rung >= 126`, correctly not triggered yet.

**The Nifty 100 ticker question is FULLY RESOLVED, not just patched.**
Earlier today `UNIVERSE["nifty100"]` was a ~93-95 name training-
knowledge approximation with 2 dead tickers removed by guesswork. It is
now a **byte-exact 100-symbol match to NSE's own official published
Nifty 100 CSV** (`tools/diagnose_nifty100_official_list.py`, real
GitHub Actions fetch against `nsearchives.nseindia.com`, confirmed via
NSE's own company-name column, not just Yahoo resolve-or-not).
`TATAMOTORS.NS` is confirmed replaced by `TMCV.NS`/`TMPV.NS` (Tata
Motors' 2025 demerger). `LTIM.NS`/LTIMindtree is confirmed genuinely
out of the current index (not a rename). Don't re-litigate this or
re-guess replacement tickers — if you suspect drift (NSE reconstitutes
the index roughly semi-annually), re-run that diagnostic, don't
hand-edit `UNIVERSE["nifty100"]`.

**Contestant count, and why two numbers are both right:**
`seed_registry()` defines **27** (mom_nifty100_lb90 included);
`ledger.json` on main has **26** live. `load_state()` backfills the gap
on the next `factory.py update()` run — this is exactly what
`health_check.py --live`'s registry-drift warning reports, and why the
new contestant doesn't show on the dashboard yet. **As of this
session's fix, that warning now prints the ledger's last-update date
so you can tell benign from broken — see RUNBOOK 1 Step 1.3a, use it,
don't just skim past the warning.**

**`factory.yml` cron: Mon-Fri 12:45 UTC, Sun 04:30 UTC.** The Sunday
run does BOTH `update()` and the weekly `report()`. If you're reading
this after Sunday 2026-08-30 ~04:30 UTC, that run should have
backfilled `mom_nifty100_lb90` and produced the first weekly report
since the contestant merged — **verify that actually happened**
(RUNBOOK 1 Steps 1.3a/1.5/1.6), don't assume it did.

**Branch is 4 commits ahead of main**, all docs/tooling, no trading
logic, no `RULES`/`LADDER`/`COST_PER_SIDE`:
`c498385` (merge-record log), `b117c8e` (Progress Artifact + its
data-generator script), `6e5ecb4` (log), `66ae914` (this session's own
low-context checkpoint). **Ask Het fresh before merging** — a prior
session's "yes" never carries forward, no matter how small the batch.

**A new, third visual surface now exists: the Progress Artifact**
(`https://claude.ai/code/artifact/e16ae3c5-4ec1-4ef3-8334-d2cf28e82989`)
— a clean, Apple-styled, real-data activity timeline (what's been
built/fixed/verified/merged), separate from the pixel-art Trading Floor
office and the Streamlit P&L dashboard. To refresh it: run
`python3 tools/build_progress_dashboard_state.py`, splice the JSON into
the existing template's `<script id="progress-data">` tag (see that
script's docstring for the exact procedure — the HTML page itself is
NOT committed to this repo, same convention as the Trading Floor
artifact), then `Artifact({action:"publish", url:"<the URL above>"})`.

## WHAT WAS LEARNED (2026-08-29 session, second half)

- **A byte-exact index basket beats an approximation, but verify
  against the PRIMARY source, not a third-party mirror.** Two
  community GitHub CSV snapshots were tried first and both were stale
  (one had tickers defunct since ~2019, the other predated the
  Nov-2022 LTI-Mindtree merger). NSE's own official archive CSV
  (`nsearchives.nseindia.com/content/indices/ind_nifty100list.csv`)
  was the actual answer, reachable only from GitHub Actions, not this
  sandbox.
- **The low-context checkpoint procedure (built earlier this session)
  was used for real, not just written and left untested.** When told
  the session was near its limit, the very first action was updating
  `loop_state.json` to `in_progress` with specific
  `resume_instructions` and pushing — before doing anything else,
  including the dashboard refresh that was also asked for. If you're
  reading this because that pattern repeats, it's working as designed.
- **A `git add -A` almost shipped inside the checkpoint script itself**
  earlier this session, before being caught and fixed — the checkpoint
  procedure now explicitly says `git status --short` first, stage by
  name. If you're about to checkpoint, don't reach for `-A`/`.`.
- **`mcp__github__actions_list` returning a huge payload regardless of
  `per_page`, and the GitHub REST API returning 403 to a bare `curl`,
  are both settled facts now** — see DO NOT RE-DERIVE below, don't
  rediscover either.

## WHAT REMAINS

Nothing structural. Phase 1 standing mode: run the schedule, let the
evidence clock run, don't add machinery. Open items are blocked on
Het, permanently gated, or passive watches — see `state.json`'s queue.
The genuinely valuable next event is **the calendar**, not a commit.

## EXACT NEXT TASK

1. Check `loop_state.json` — if still `in_progress`, finish RUNBOOK 5
   (it wasn't completed before this session ended) before anything else.
2. Otherwise, run **RUNBOOK 1** (hourly check-in). If clean and nothing
   changed, say "Nothing new" in one or two sentences and stop.
3. Specifically confirm on the first run after Sunday 2026-08-30
   ~04:30 UTC: did `mom_nifty100_lb90` land in `ledger.json`, and did
   the weekly report run? (See CURRENT STATE above.)
4. Ask Het whether to merge the 4 pending branch commits.

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
  bitten twice). Read the warning's date comparison, don't just skim it
  (RUNBOOK 1 Step 1.3a).
- Synthetic regression pattern: copy `factory_state/` + `factory.py`
  into an isolated scratch dir, monkeypatch `fetch_prices()` with
  synthetic data (inject shock days if testing event_drift-family
  changes), run 40 `update()` cycles + `report()`, assert no crash and
  check new/changed entries behave correctly. Exact snippet in
  RUNBOOK 4 Step 4.3.
- Dashboard changes: `streamlit run dashboard.py`, then verify via a
  real headless-browser screenshot (Playwright, pre-installed at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) — don't just
  check for import errors. `pkill -f "streamlit run dashboard.py"` can
  match its own shell and kill the rest of your command silently —
  verify anything chained after it actually ran.
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
- You're below ~20-30% of usable session context — see RUNBOOKS.md's
  "RUNNING LOW ON CONTEXT" section immediately, checkpoint BEFORE
  anything else, not after.

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
- The current, real, NSE-verified `UNIVERSE["nifty100"]` basket
  (100 symbols, see CURRENT STATE above) — don't re-guess tickers,
  re-run the diagnostic if you suspect drift.

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
- Three visual surfaces now exist, each with different content — don't
  conflate them: Streamlit `dashboard.py` (P&L/portfolio, Apple-ish),
  the Trading Floor Artifact (pixel/retro agent office), and the
  Progress Artifact (Apple-styled real activity timeline, see CURRENT
  STATE above).
