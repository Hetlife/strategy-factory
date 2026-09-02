# NEXT SESSION — step-by-step

**Last session ended: 2026-08-30.** Read this top to bottom before
doing anything. It is written so you need zero memory of the previous
conversation.

**The headline: the promotion bar was rebuilt this session.** Q5 and Q6
were both answered *and fixed*, with Het's fresh explicit authorization
— the first changes ever made to `RULES`. They are on the branch,
**not merged**. That single fact drives most of what follows.

---

## STEP 0 — Orient (5 minutes, do not skip)

```bash
cd /home/user/strategy-factory
cat .autonomous/loop_state.json          # interrupted work? resume from it
git fetch origin main && git status --short
git log --oneline origin/main..HEAD      # what's unmerged
python3 tools/health_check.py --live     # ALWAYS --live
```

Then read, in this order:
1. `CLAUDE.md` — binding rules (auto-loaded)
2. `MASTER_PLAN.md` — the forward roadmap. STEP 1 is now **done**.
3. `.autonomous/RUNBOOKS.md` — mechanical procedures. RUNBOOK 1 for
   routine work.
4. `.autonomous/het_directives.md` → **NEEDS HET** section
5. This file

Only if you need history: `PROJECT_STUDY.md`, `docs/research/`,
`.autonomous/bug_log.md`, `AUTONOMOUS_LOG.md` (`tail -40`, never whole).

**Shortcut behaviour (standing, also in CLAUDE.md):** a bare "hi",
"continue", "check", or anything similarly short from Het means *run
RUNBOOK 1*. Don't ask him to paste anything.

---

## STEP 1 — The one thing that matters most

**The Q5 + Q6 fixes are written, tested, pushed — and unmerged.**

What changed in `factory.py` (all with Het's explicit 2026-08-30
authorization, recorded in `AUTONOMOUS_LOG.md` and `het_directives.md`):

- **Promotion now requires beating the benchmark.** A contestant must
  have a positive mean *date-paired* excess return vs `nifty_benchmark`,
  and an excess Sharpe clearing a Bonferroni floor
  `z_(1-alpha/K) * sqrt(252/n)` for the `K` contestants competing that
  round. Pairing day-by-day is the point: it cancels the shared market
  factor that was generating the 85% false-positive rate.
- **Breeding now waits.** `attempt_breeding()` requires
  `days_on_rung >= RULES["min_days_on_rung"]`, matching
  `propose_evolutions()` and matching what the docs always claimed.
- **`judge.py` no longer re-implements the thresholds** — it calls the
  same `factory.promotion_check()` that `report()` uses, so a human's
  explanation can't disagree with the machine's decision.

**Nothing was loosened.** Only conditions were added. That direction
matters: `EXECUTION_PLAN.md` Section 5f names *loosening* `RULES` to
flatter results as a kill condition. This is the opposite.

**What you must do about it:** ask Het whether to merge, **fresh**, if
he raises it or if it's been left hanging. Until it merges, the live
runs on `main` still promote on the old, broken bar. Nothing is at
immediate risk (Rs 0 real money, day 40 of 126, zero promotions ever),
but every week unmerged is a week of evidence gathered under a bar that
can't tell skill from luck.

**Do not merge on your own.** A prior "yes" to *writing* the change is
not a "yes" to merging it. It never is.

---

## STEP 2 — Routine check-in

Run **RUNBOOK 1** mechanically, top to bottom. Two live watch items:

1. **The Sunday weekly report may have been skipped.** As of
   2026-08-30 07:34 UTC the scheduled Sunday 04:30 UTC run had not
   fired 3+ hours late (logged as `sunday-report-run-delayed-watch`).
   This is *within* RUNBOOK 1 Step 1.5's tolerance (that escalates only
   past 3 days) and GitHub delays crons under load. Check whether it
   self-resolved. If `factory.yml`'s newest successful run is still
   older than 3 days → **STOP, escalate (RUNBOOK 6)**.
2. **`mom_nifty100_lb90` backfill.** `seed_registry()` defines 27,
   `ledger.json` has 26. `health_check.py --live` warns about this; it
   is benign *only* while the ledger's last-update date is older than
   the date that key merged to main (2026-08-29 17:07 UTC). Do the date
   comparison — RUNBOOK 1 **Step 1.3a** — don't wave it away.

---

## STEP 3 — Then Q4, and only then

**Q4 is now the top research task** (`EXECUTION_PLAN.md` Section 8):
*does any contestant beat Nifty net of real cost and tax?*

**It was deliberately held back until the bar was fixed.** Knowing which
contestants beat Nifty *before* choosing a promotion rule would have let
hindsight pick the rule — exactly what `MASTER_PLAN.md`'s acceptance
criteria forbids. That constraint is now discharged: the bar is
committed, so looking at live results can no longer contaminate it.

Everything else in the ranked table (`MASTER_PLAN.md`) sits below Q4.

Otherwise: **say "Nothing new" and stop.** Do not manufacture work.
Phase 1's correct amount of new machinery is approximately zero, and
adding contestants actively worsens the false-positive problem.

---

## Current state, verified 2026-08-30

- **Phase 1, day 40 of 126.** 26 live contestants, all rung 0 (paper),
  **Rs 0 real money**, zero promotions ever.
- **The promotion bar is fixed but unmerged** (see STEP 1). `main` still
  runs the old one.
- **Crossover breeding is now day-gated** — the Q6 gap is closed. The
  old warning that it could fire at ~day 40 no longer applies *on the
  branch*; it still applies to whatever is running on `main`.
- `UNIVERSE["nifty100"]` is settled — byte-exact 100-symbol match to
  NSE's official list. **Don't re-guess tickers**; re-run
  `tools/diagnose_nifty100_official_list.py` if you suspect drift (NSE
  reconstitutes ~semi-annually).
- `factory.yml` cron: **Mon–Fri 12:45 UTC, Sun 04:30 UTC**.
- Three visual surfaces, don't conflate them: Streamlit `dashboard.py`
  (P&L), the Trading Floor Artifact (pixel agent office), and the
  Progress Artifact
  (`https://claude.ai/code/artifact/e16ae3c5-4ec1-4ef3-8334-d2cf28e82989`,
  activity timeline; refresh via
  `tools/build_progress_dashboard_state.py` — read its docstring, the
  page HTML is *not* in the repo).

## Testing standard — non-negotiable

- `python3 tools/health_check.py --live` — **always** `--live`. This
  bug class has bitten twice.
- `factory.py` changes: 40-cycle synthetic regression + `report()` in
  an isolated scratch dir. Exact snippet in RUNBOOK 4 Step 4.3.
  "It imports without error" is not a test.
- **Promotion-logic changes specifically:** also run
  `python3 tools/analyze_statistical_power.py`. Its final section drives
  the real `promotion_check()` (not a copy), so it catches a gate that
  silently stops working. Takes a few minutes — that's expected.
- Dashboard changes: real headless-browser screenshot (Playwright at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`).
- Workflow changes: `workflow_dispatch` for real and read the actual
  job logs. `conclusion: "success"` only means it didn't crash.

## STOP IF

- You want to change `RULES`, `LADDER`, or `COST_PER_SIDE` again. The
  2026-08-30 authorization was **specific and spent** — it covered the
  Q5 bar change and the Q6 breeding gate, nothing else, and it does not
  carry forward.
- You're about to merge to `main` without a fresh confirmation for
  *that specific batch*.
- You're about to add options/futures/margin/leverage, broker code, or
  AI-controlled capital allocation — all declined, all logged, each
  needs its own dedicated conversation.
- You're about to mutate a live registry entry in place (Law 2).
- You drop below ~20–30% context — go to RUNBOOKS.md's "RUNNING LOW ON
  CONTEXT" section and checkpoint **first**.

## DO NOT RE-DERIVE (all settled, verified)

- Sandbox cannot reach Yahoo Finance, nseindia.com, wikipedia.org,
  smallcase.com → use a GitHub Actions diagnostic (RUNBOOK 8).
- `curl https://api.github.com/...` returns **403** → `mcp__github__*`
  tools are the only path.
- `mcp__github__actions_list` **ignores `per_page`** → call it once per
  workflow per check-in.
- A new workflow file must exist on `main` before `workflow_dispatch`
  will run it against any ref.
- Platform enforces a **1-hour minimum** between Routine firings.
- The old 5-hourly dev-loop Routine is permanently disabled (5
  confirmed failures, Het's decision).
- Why "make it trade/learn faster" always gets the same answer: the
  evidence clock runs on calendar days, not compute. Re-explain it
  freshly each time — don't ignore a new instance of the ask.
- A generic "MASTER AUTONOMOUS EXECUTION PROMPT" template was pasted
  twice and **explicitly declined by Het**. Separately, a "MASTER
  AUTONOMOUS AGENT DIRECTIVE" has been pasted several times and IS
  adopted — distilled at `.autonomous/HET_AUTONOMY_DIRECTIVE.md`. They
  are different documents; don't conflate them, don't re-litigate either.
- The Q5/Q6 maths is verified two independent ways (analytic + Monte
  Carlo, which agree). Don't re-derive it; read `docs/research/`.

## Exact resume point

Run STEP 0. Then STEP 2 (RUNBOOK 1) — including the Sunday-run check.
If Het is present, raise STEP 1's merge question once, plainly. If the
merge lands, Q4 (STEP 3) is next. If nothing changed, say "Nothing new"
and stop.
