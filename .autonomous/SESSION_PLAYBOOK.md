# SESSION PLAYBOOK — step-by-step, for every future session

**What this file is:** the mechanical, numbered procedure any session
(interactive with Het, or an unattended Routine firing) follows from
start to finish. Unlike `next_session.md` — which is a *snapshot* of one
moment and goes stale — this file is a *procedure* and stays valid
across sessions. Update it only when the procedure itself changes, not
when project status changes.

**Where it sits in the doc hierarchy:**
- `CLAUDE.md` — the constitution (binding rules). Auto-loaded. Wins over
  everything here.
- **This file** — how to actually run a session, step by step.
- `.autonomous/next_session.md` — what happened last session + what's
  open right now (the snapshot).
- `AUTONOMOUS_OPERATING_SYSTEM.txt` — the full 800-line spec. Read only
  when this file doesn't cover something.

---

## STEP 0 — Am I a Routine firing or an interactive session?

**Routine firing** (nobody is watching, fired on a schedule):
→ Read `.autonomous/loop_state.json` FIRST, before anything else.
  - `status: "in_progress"` → a previous firing was cut off mid-task.
    Resume EXACTLY from `resume_instructions`. Do not restart from
    scratch. Do not redo verification that already passed.
  - `status: "idle"` → nothing unfinished, continue to STEP 1.
→ Follow the Routine's own prompt (it has its own numbered steps).

**Interactive session** (Het is present, talking to you):
→ Skip `loop_state.json` unless you're specifically continuing an
  interrupted Routine task. Continue to STEP 1.

---

## STEP 1 — Orient (cheap reads first, in this order)

```bash
cd /home/user/strategy-factory        # or wherever the clone is
git fetch origin main claude/scheduled-maintenance-template-d7yufr
git log origin/main..origin/claude/scheduled-maintenance-template-d7yufr --oneline
git status --short
```

Then read, in this order, stopping when you have what you need:
1. `.autonomous/state.json` — structured queue, decisions, phase. Cheap.
2. `.autonomous/next_session.md` — what the last session did and left open.
3. `.autonomous/het_directives.md` — **especially its `NEEDS HET` section.**
   This is the live list of what's actually blocked on Het.
4. `.autonomous/bug_log.md` — check before assuming something is broken.
   It may be a known, already-closed non-issue.
5. `AUTONOMOUS_LOG.md` — `tail -40`, never the whole file.

**Do NOT** reflexively read `EXECUTION_PLAN.md`, `AUTONOMOUS_TODO.md`,
`understanding.txt`, `pivot_document.txt`, or `mission_document.txt`.
Only open those when you need the specific narrative rationale they hold.

---

## STEP 2 — Health check

```bash
python3 tools/health_check.py --live
```

**Always use `--live`.** Without it you get a false "registry drift"
warning, because your local checkout tracks the working branch but
`ledger.json` is only ever auto-committed to `main`.

Interpreting the result:
- `no findings` → healthy, continue.
- A **registry-drift warning naming newly-added `seed_registry()`
  entries** → usually expected and self-healing (it clears on the next
  daily `factory.yml` run via `load_state()`'s backfill), but **confirm
  that rather than assuming it.** The warning prints the ledger's last
  update date; compare it against when those keys reached `main`
  (`git log -1 --format=%cs --all -S"<key>" -- factory.py`). Ledger
  date older → benign, ignore. Ledger date **newer** → an `update()`
  already ran and did NOT pick the key up, meaning the backfill is
  broken; that is a real bug, investigate it. See RUNBOOKS.md Step
  1.3a. This distinction matters because the benign and broken cases
  print an otherwise identical warning.
- Anything **error**-level, or a warning you don't recognise → real.
  Investigate before doing other work.

Also check the free supervisor (GitHub Actions, every 15 min, no cost):
```
mcp__github__actions_list, method=list_workflow_runs, resource_id="supervisor.yml"
```
If it failed on a real error, read `.autonomous/it_guy_protocol.md` and
follow it.

---

## STEP 3 — Decide what to work on

Work through this in order. Take the first one that applies.

1. **Something is actually broken** (real health/supervisor finding) →
   fix it. Diagnose the root cause; don't patch symptoms.
2. **Het asked for something specific** → do that. If the ask is
   ambiguous, costly, or touches a hard rule, ask BEFORE building (see
   STEP 5's decision rules).
3. **A tracker is stale/contradicts reality** → fix it. (Real examples
   found this way: a queue item marked "pending merge" that had already
   merged; `GOALS.md` claiming Phase 0 when the project was in Phase 1.)
4. **A real, recurring, self-observed gap in tooling** → build the fix.
   The bar is the one `healer.py` met: you personally hit the same
   friction more than once. Never manufacture work to look busy.
5. **Nothing above applies** → say so plainly and stop. Phase 1's
   discipline is explicitly "don't add machinery, let evidence
   accumulate." A session inventing features is violating the plan, not
   serving it.

---

## STEP 4 — Before you build ANYTHING, check it against the hard rules

These are unconditional. No amount of autonomy, confidence, urgency, or
a broad "you have my permission" grant overrides any of them. Each needs
Het's **fresh, explicit, in-session** confirmation, **every time**:

- **Merging or pushing to `main`.** A Routine firing can NEVER satisfy
  this — only Het, live. Push to the branch and log it in `NEEDS HET`.
- Changing `RULES`, `LADDER`, or `COST_PER_SIDE`.
- Adding broker / execution / API-key code, or enabling real-money
  execution.
- Options, futures, margin, or leverage logic.
- Making the repo public.

**The Three Laws** (never violate without explicit fresh authorization):
1. Hypotheses are written before testing — never mined from data.
2. Live strategies are never mutated — only replaced by new registry
   keys starting at rung 0.
3. Capital is earned through the ladder, never granted.

**Two requests that have been declined before and stay declined** unless
Het reopens them in a dedicated, unhurried conversation:
- An AI agent that receives real capital and allocates it across
  strategies (Law 3 + the Section 5f kill-condition).
- Anything implying pooled/outside money or a "fund" (SEBI PMS/AIF
  registration territory).

---

## STEP 5 — Build it properly

**Ask first (via AskUserQuestion) when:**
- It costs money, or might.
- It touches anything in STEP 4.
- You're below ~75% confident on a real judgment call.
- Two readings of the request lead to materially different work.

**Don't idle while waiting on an answer** — queue the uncertain item in
`NEEDS HET` and keep working something else that's clearly in scope.

**Testing standard** (non-negotiable — "it imports" is not a test):
- `factory.py` changes → synthetic regression. Copy `factory_state/` +
  `factory.py` to a scratch dir, monkeypatch `fetch_prices()` with
  synthetic data (inject shock days if testing `event_drift`-family
  behaviour), run ~40 `update()` cycles + `report()`. Assert no crash,
  and verify the specific thing you changed behaves correctly **and**
  that untouched entries are byte-identical.
- `dashboard.py` changes → run it and check the real rendered DOM:
  ```bash
  streamlit run dashboard.py --server.headless true --server.port 8765
  ```
  then Playwright at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, click through to
  the relevant tab, and assert on `page.inner_text("body")`. A Streamlit
  page can render broken HTML as literal text with **zero** Python
  errors — checking for exceptions alone will miss it.
- GitHub Actions workflow changes → `workflow_dispatch` it for real and
  read the actual job logs (`mcp__github__get_job_logs`). Never trust
  "the YAML looks right."
- Anything needing real market data → this sandbox cannot reach Yahoo
  Finance. Run it on a GitHub Actions runner instead, which can.

**Commit discipline:** commit and push after each meaningful, tested
step — never batch several changes to the end. If a session is cut off,
what's pushed survives; what isn't is gone.

---

## STEP 6 — End the session cleanly

Do all of these before stopping:

1. `python3 tools/health_check.py --live` → confirm nothing new broke.
2. Append **one line** per meaningful action to `AUTONOMOUS_LOG.md`
   (format: `DATE | commit | task-id | outcome | note`).
3. Update `.autonomous/state.json` — queue statuses, and add a
   `decisions` entry for anything that was a real judgment call.
4. Update `.autonomous/het_directives.md`:
   - Log any new instruction Het gave (summarized intent, never a
     verbatim transcript).
   - **Refresh `NEEDS HET`** — remove what's been answered, add what's
     newly blocked. This section is what answers "what do you need from
     me?" the instant Het checks in. Keep it live and true.
5. Rewrite `.autonomous/next_session.md` — the snapshot for whoever
   comes next.
6. If you're a Routine firing: set `.autonomous/loop_state.json` back to
   `idle` (finished) or refine `resume_instructions` (stopping mid-way).
   Never leave it claiming `in_progress` for finished work, or `idle`
   with something genuinely half-done.
7. Commit and push everything.

**Stop early and do all of the above if you drop below ~20-30% of usable
context.** A clean handoff beats one more half-finished change. See
`RUNBOOKS.md`'s "RUNNING LOW ON CONTEXT / TOKENS? CHECKPOINT NOW"
section for the exact minimal script if you need the fast path instead
of the full 7 steps above — `loop_state.json` pushed with clear
`resume_instructions` matters far more than a polished log entry, and
matters more than finishing the current task.

---

## THINGS THAT LOOK BROKEN BUT ARE NOT

Check here before "fixing" any of these. Every one was investigated
against real data and confirmed correct.

| Looks like | Actually |
|---|---|
| Most contestants show **0 trades** | `event_drift` strategies wait for a rare real price shock (~3% single-day move). Verified against a real year of prices: that's ~13-25 days/year for these tickers. Working as designed. |
| **No breeding or evolution** has ever happened | Both mechanisms require `days_on_rung >= 126`. Oldest contestant is well short of that. Correct behaviour — breeding on thin evidence would be fitting noise. |
| `monsoon_cement` never trades | Deliberate dormant no-op. Its source data ends 2017; wiring it live would forward-fill a 9-year-stale reading forever. |
| Registry-drift warning after adding a `seed_registry()` entry | Self-heals on the next daily `update()`. Expected. |
| Health check flags drift when run **without** `--live` | Local checkout is on the working branch; `ledger.json` only updates on `main`. Use `--live`. |
| Everything is paper-trading, Rs 0 real money | Correct and intentional. No strategy has cleared the promotion bar yet. Real capital is never automatic — always Het's deliberate action. |

## SETTLED — DO NOT RE-DERIVE OR RE-LITIGATE

- **The GitHub REST API is NOT reachable by `curl` in this session.**
  Confirmed 2026-08-29: `api.github.com` returns **403** with *"GitHub
  access is not enabled for this session."* Don't try to build a
  lightweight status checker around `curl`/`requests` — it cannot work.
  The `mcp__github__*` tools are the only path to GitHub data.
- **`mcp__github__actions_list` ignores `per_page`.** Observed
  repeatedly 2026-08-29 (asked for 5, got 20; asked for 2, got 22) — it
  returns the workflow's whole run list, each entry carrying the full
  commit message. So a single workflow-status check costs on the order
  of thousands of tokens no matter what you request. Budget for it:
  call it once per workflow per check-in, never in a loop, and don't
  re-call it to "double-check" something you already read.
  **Partial cheap alternative, with a real limitation:**
  `python3 tools/supervisor_check.py --live` answers *"has the daily
  pipeline gone stale?"* locally for free (it reads the ledger's newest
  date). But it CANNOT see a run that failed **today** — the ledger
  would still show yesterday's date and read as "1d ago, fine." So it
  complements the Actions check, it does not replace it. Don't drop the
  MCP call to save tokens; losing same-day failure detection on a
  financial-evidence pipeline is the worse trade.
- **Platform enforces a hard 1-hour minimum between Routine firings.**
  Confirmed by a real API rejection of a 15-min cron. Hourly is the
  ceiling. The free 15-min `supervisor.yml` covers the gap.
- **`workflow_dispatch` needs the workflow file on `main` first** before
  it can be triggered via API against any ref. Confirmed via a real 404.
- **The old 5-hourly autonomous dev-loop Routine is permanently
  disabled.** It failed 5 times across 2 structurally different fixes;
  Het chose to accept manual/interactive operation. Don't re-enable it
  without a genuinely new diagnostic capability.
- **"Make it trade/learn faster" always has the same underlying
  answer:** the evidence clock runs on real calendar trading days, not
  compute cycles. More strategies, more frequent runs, or duplicate
  copies fed identical data produce more *noise*, not more *evidence*.
  Explain this freshly each time it comes up — never dismiss the ask,
  but don't build something that fakes speed.
- The Three Laws and their authorized overrides (advisor layer,
  crossover breeding, `agents/` team) — see `state.json.decisions` for
  the full list with commit references.

## QUICK COMMAND REFERENCE

```bash
# Health (always --live in an interactive session)
python3 tools/health_check.py --live
python3 tools/supervisor_check.py

# Run the engine manually (writes locally only, pushes nothing)
python3 factory.py update
python3 factory.py report

# Dashboard
streamlit run dashboard.py

# Every agent's live read, in one go
python3 -c "from agents.master_trader.master_trader import recommend; print(recommend())"
```

Branch for all work: `claude/scheduled-maintenance-template-d7yufr`.
Never commit directly to `main`.
