# NEXT SESSION — step-by-step

**Last session ended: 2026-08-29.** Read this top to bottom before
doing anything. It is written so you need zero memory of the previous
conversation.

---

## STEP 0 — Orient (5 minutes, do not skip)

Run these, in this order:

```bash
cd /home/user/strategy-factory
cat .autonomous/loop_state.json          # interrupted work? see STEP 1
git fetch origin main && git status --short
git log --oneline origin/main..HEAD      # what's unmerged
python3 tools/health_check.py --live     # ALWAYS --live
```

Then read, in this order:
1. `CLAUDE.md` — binding rules (auto-loaded)
2. **`MASTER_PLAN.md`** — *new this session.* The forward roadmap and
   why STEP 1 below is blocking everything else.
3. `.autonomous/RUNBOOKS.md` — the mechanical procedures. Start at
   RUNBOOK 1 for routine work.
4. `.autonomous/het_directives.md` → **NEEDS HET** section
5. This file

Only if you need history or precedent: `PROJECT_STUDY.md`,
`docs/research/`, `.autonomous/bug_log.md`, `AUTONOMOUS_LOG.md`
(`tail -40`, never the whole thing).

**Shortcut behaviour (standing, also in CLAUDE.md):** a bare "hi",
"continue", "check", or anything similarly short from Het means *run
RUNBOOK 1*. Don't ask him to paste anything.

---

## STEP 1 — The one thing that matters most

**Read `docs/research/Q5_statistical_power.md`.** It was written last
session and it changes the project's priorities.

**The finding, in one line:** at the current 126-day bar with 26
contestants, the promotion gate promotes a *pure-noise* contestant
~85% of the time. It cannot currently tell skill from luck.

**What you must do about it:** nothing, unilaterally. It requires
changing `RULES`, which is a hard rule — Het's explicit, separate
authorization only. Your job is to make sure it's in front of him:

- It is the **top item** in `het_directives.md`'s NEEDS HET section.
- If Het is present and hasn't decided: raise it. Plainly, once, without
  nagging. Say what it means (a promotion right now would probably be
  luck) and that the recommended fix — require beating
  `nifty_benchmark` plus a multiplicity correction — **costs no
  calendar time**, unlike the alternative of waiting ~3 years.
- If Het decides: implement, test (re-run
  `tools/analyze_statistical_power.py` against the new gate and show
  the false-positive rate under ~10%), **and do it before looking at
  which current contestants it would promote or fail** — that ordering
  is what keeps it free of hindsight bias. Then ask separately before
  merging.
- If Het isn't around: do **not** treat silence as approval. Carry on
  with routine work and leave it flagged.

---

## STEP 2 — Routine check-in

Run **RUNBOOK 1** mechanically, top to bottom. Two things specifically
worth verifying on the first run after **Sunday 2026-08-30 ~04:30 UTC**
(that run does both `update()` and the weekly `report()`):

1. Did `mom_nifty100_lb90` finally land in `ledger.json` on main?
   `health_check.py --live` should go fully clean when it does — the
   registry-drift warning disappears on its own.
2. Did the weekly `report()` run and commit? It's the first report
   since the new contestant merged.

**Do not skim past the registry-drift warning.** It now prints the
ledger's last-update date so you can tell benign from broken — see
RUNBOOK 1 **Step 1.3a** and actually do that date comparison.

---

## STEP 3 — Ask about the unmerged commits

**14 commits sit on the branch, unmerged** (run
`git log --oneline origin/main..HEAD` for the current list — that
number will be stale). All docs/tooling/analysis — no trading logic,
no `RULES`/`LADDER`/`COST_PER_SIDE`. Includes the Q5 analysis, the
Progress Artifact tooling, `MASTER_PLAN.md`, `MASTER_PROMPT.md`.

**Het was asked on 2026-08-29 and said NO — leave them on the branch.**
That is a deliberate, recorded choice, not an oversight. Nothing breaks:
the daily runs, the automation and the hourly Routine are unaffected,
and future sessions read this branch anyway. **Do not re-ask on your
first check-in** — it would just be nagging. Only raise it again if
something actually changes (he asks, or a merge becomes genuinely
necessary for a specific task, e.g. dispatching a brand-new workflow,
which requires the file to exist on `main` first).

When it does come up again: ask fresh. A prior session's "yes" never
carries forward, no matter how small the batch or how broad a
permission grant sounded.

---

## STEP 4 — If there's genuinely nothing else

**Q6 is the best unprompted next task** (`EXECUTION_PLAN.md` Section 8,
ranked in `MASTER_PLAN.md`): *do the three evolution mechanisms
increase overfitting risk at this sample size?* Same failure family as
Q5, free to answer, and the answer could justify disabling a breeding
mechanism during Phase 1 rather than letting it manufacture more
lottery tickets. Analysis only — it changes no live behaviour without
Het.

Otherwise: **say "Nothing new" and stop.** Do not manufacture work.
Phase 1's correct amount of new machinery is approximately zero, and
adding contestants actively makes the false-positive problem worse
(Q5: 26 → 40 contestants moves it from 84% → 89%).

---

## Current state, verified 2026-08-29

- **Phase 1, day 40 of 126.** 26 live contestants, all rung 0 (paper),
  **Rs 0 real money**, zero promotions ever.
- **Crossover breeding is NOT 126-day-gated** (found 2026-08-29, see
  `docs/research/Q6_breeding_overfitting.md`). It needs only
  `equity > 1.0` AND `trades >= 10`, and could fire within weeks.
  `mom_cement_lb60` (13 trades) needs only to turn profitable. This
  contradicts what the docs said in three places, now corrected.
- `seed_registry()` defines **27**, `ledger.json` has **26** — the gap
  is `mom_nifty100_lb90`, backfilled by the next `update()` run. Both
  numbers are correct; this is the registry-drift warning, not a bug.
- **`UNIVERSE["nifty100"]` is settled** — a byte-exact 100-symbol match
  to NSE's own official published list, verified via GitHub Actions.
  `TMCV.NS`/`TMPV.NS` are the real Tata Motors successors; LTIMindtree
  is genuinely out of the index. **Don't re-guess tickers** — re-run
  `tools/diagnose_nifty100_official_list.py` if you suspect drift (NSE
  reconstitutes ~semi-annually).
- `factory.yml` cron: **Mon–Fri 12:45 UTC, Sun 04:30 UTC**.
- Three visual surfaces, don't conflate them: Streamlit `dashboard.py`
  (P&L), the Trading Floor Artifact (pixel agent office), and the
  Progress Artifact
  (`https://claude.ai/code/artifact/e16ae3c5-4ec1-4ef3-8334-d2cf28e82989`,
  activity timeline; refresh via
  `tools/build_progress_dashboard_state.py` — see its docstring).

## Testing standard — non-negotiable

- `python3 tools/health_check.py --live` — **always** `--live`. This
  bug class has bitten twice.
- `factory.py` changes: 40-cycle synthetic regression + `report()` in
  an isolated scratch dir. Exact snippet in RUNBOOK 4 Step 4.3.
  "It imports without error" is not a test.
- Dashboard changes: real headless-browser screenshot (Playwright at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`).
- Workflow changes: `workflow_dispatch` for real and read the actual
  job logs. `conclusion: "success"` only means it didn't crash — not
  that the result was good news.

## STOP IF

- You want to change `RULES`, `LADDER`, or `COST_PER_SIDE` — **except**
  implementing a STEP 1 fix Het has explicitly authorized.
- You're about to merge to `main` without a fresh confirmation for
  *that specific batch*.
- You're about to add options/futures/margin/leverage, broker code, or
  AI-controlled capital allocation — all declined, all logged, each
  needs its own dedicated conversation.
- You're about to mutate a live registry entry in place (Law 2 —
  corrupts accumulated evidence; add a new key instead).
- You drop below ~20–30% context — go to RUNBOOKS.md's "RUNNING LOW ON
  CONTEXT" section and checkpoint **first**, before anything else.

## DO NOT RE-DERIVE (all settled, verified)

- Sandbox cannot reach Yahoo Finance, nseindia.com, wikipedia.org,
  smallcase.com → use a GitHub Actions diagnostic (RUNBOOK 8).
- `curl https://api.github.com/...` returns **403** → `mcp__github__*`
  tools are the only path.
- `mcp__github__actions_list` **ignores `per_page`** and returns
  everything → call it once per workflow per check-in.
- A new workflow file must exist on `main` before `workflow_dispatch`
  will run it against any ref.
- Platform enforces a **1-hour minimum** between Routine firings.
- The old 5-hourly dev-loop Routine is permanently disabled (5
  confirmed failures, Het's decision).
- Why "make it trade/learn faster" always gets the same answer: the
  evidence clock runs on calendar days, not compute. Re-explain it
  freshly each time it comes up — don't ignore a new instance of the ask.
- A generic "MASTER AUTONOMOUS EXECUTION PROMPT" template was pasted
  twice and **explicitly declined by Het** for this project. Don't
  re-litigate if it resurfaces.

## Exact resume point

Run STEP 0. Then STEP 1 (raise Q5 if Het is present), then STEP 2
(RUNBOOK 1). If both are done and nothing changed, say "Nothing new"
and stop.
