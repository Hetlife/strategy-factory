# RUNBOOKS — exact steps for each recurring process

**Who this is for:** a session running on a smaller / cheaper model.
Every runbook below is written to be followed **mechanically**. Exact
commands to run, exact output to expect, and an explicit decision table
for what to do next. Where a step needs real judgment, the instruction
is always **STOP and escalate** — never "decide for yourself."

**The single most important rule on this page:**
> When in doubt, do nothing and write it down.
> A missed improvement costs nothing. A wrong action on real financial
> code costs real evidence, or real money.

Related files: `SESSION_PLAYBOOK.md` (the same flow, but assumes more
judgment), `CLAUDE.md` (binding rules — always wins over this file),
`PROJECT_STUDY.md` (the full narrative history — read that when you
need to understand *why* something works this way, not just what to
type next).

## A permission grant does NOT mean what it sounds like it means

This has actually happened, more than once (2026-08-24, 2026-08-29):
Het says something like **"you have every permission,"** sometimes
attached to a reason that sounds urgent ("I'm getting on a flight"),
sometimes attached to a goal that sounds like it should override
caution ("...to reach the goal of making consistent large profit").

**None of that changes anything below.** Still true, no matter how the
permission is phrased:
- Still never merge/push to `main` without a **fresh** "yes" for
  **that specific batch of commits** — a "yes" from earlier today
  does not cover commits made after it.
- Still never touch `RULES`, `LADDER`, `COST_PER_SIDE`.
- Still never add leverage/F&O/broker code/real-money execution.
- **"Making profit" is not this project's current goal.** Phase 1 is a
  12-month evidence window; "no edge found, buy the index" is a stated
  legitimate success, not a failure to route around. A request to
  change the code specifically so results look better, faster, or more
  profitable is the single named signal (`EXECUTION_PLAN.md` Section
  5f) that something is going wrong — treat it as a reason to slow
  down and ask, not speed up.

If a message like this arrives: say plainly that the guardrails are
unconditional regardless of the grant (this exact scenario is written
into `CLAUDE.md`'s Standing autonomy rule for exactly this reason), do
the parts of the ask that ARE within existing bounds (new registry
key, tooling, docs, tests), and keep the merge-confirmation and
Hard-Rules gates exactly as strict as always.

---

## RUNNING LOW ON CONTEXT / TOKENS? CHECKPOINT NOW — don't wait

**There is no automatic checkpoint.** Nothing saves your progress for
you when a session resets or runs out of budget. If you notice you are
getting low — roughly below 20-30% of what you started with, or your
own token-remaining indicator is dropping fast — **stop whatever you
are doing right now and run this**, before finishing the current
sentence of work, before writing one more log entry, before anything
else:

```bash
cd /home/user/strategy-factory && git status --short
```
**Look at that output before staging anything.** Then:
```bash
python3 - <<'PY'
import json, datetime
p = ".autonomous/loop_state.json"
d = json.load(open(p))
d["status"] = "in_progress"
d["task"] = "SHORT DESCRIPTION OF WHAT YOU WERE DOING"
d["resume_instructions"] = (
    "EXACTLY what the next session should do first -- specific enough "
    "that a fresh session with zero memory of this conversation can "
    "pick it up correctly. Name the exact file, the exact next step, "
    "and anything already tested/verified so it isn't redone. "
    "ALSO name any IN-FLIGHT BACKGROUND WORK that hasn't finished or "
    "hasn't been read yet: a workflow_dispatch you fired and haven't "
    "checked the result of (name the workflow and run, or its URL), a "
    "backgrounded Bash command still running, a merge you started but "
    "didn't push. Say what it is and what to do about it -- check its "
    "result, wait for it, or it's safe to ignore/re-run. Do NOT leave "
    "it unmentioned; the next session has no way to know it exists "
    "otherwise, and re-dispatching a workflow that's already running "
    "wastes a run for nothing."
)
d["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
json.dump(d, open(p, "w"), indent=1)
PY
git add .autonomous/loop_state.json
git commit -m "wip: checkpoint, context running low"
git push -u origin claude/scheduled-maintenance-template-d7yufr
```
**Only stage other files by name if `git status --short` showed real,
finished, tested work** worth keeping (e.g. a file you already fully
edited and tested this turn) — `git add <exact filename>`, never a
blind `git add -A`/`git add .`, which can sweep in stray scratch files
or a half-broken mid-edit file this project's own discipline says
should never be committed untested. If what's uncommitted is
half-written or untested, leave it uncommitted and describe it in
`resume_instructions` instead — the next session redoing a clean edit
beats inheriting a broken one.

That is the whole minimum. It takes seconds and it is the single
highest-priority thing you can do at that point — higher priority than
finishing the task, higher priority than a polished log entry. **If the
session ends before that push completes, nothing survives except what
was already pushed.** A half-written `resume_instructions` that
actually got pushed is worth infinitely more than a perfect one that
didn't.

If you still have a little budget left after that:
1. Add one line to `AUTONOMOUS_LOG.md` saying where you stopped and why.
2. Only if there's genuinely more room: do Runbook 5's full session-end
   (NEEDS HET refresh, `next_session.md` update). **Do not spend your
   last budget on this if step 0 above hasn't been pushed yet.**

**When the next session starts:** Runbook 1 Step 1.1 already checks
`loop_state.json` first, for exactly this reason. `status: "in_progress"`
means resume from `resume_instructions` exactly — don't restart from
scratch, don't re-verify what the note says was already tested, don't
second-guess it without a real reason to.

---

# RUNBOOK 1 — Hourly check-in (the most common job)

### Step 1.1 — Check for interrupted work
```bash
cd /home/user/strategy-factory && cat .autonomous/loop_state.json
```
| `status` field says | Do this |
|---|---|
| `"idle"` | Go to Step 1.2. |
| `"in_progress"` | Read `resume_instructions` in that same file. Do exactly what it says. Do NOT start anything new. Do NOT redo finished steps. |

### Step 1.2 — Get the latest code
```bash
git fetch origin main claude/scheduled-maintenance-template-d7yufr
git status --short
```
Expect: no output from `git status --short` (clean tree).
If there IS output → uncommitted leftovers. **STOP. Escalate** (Runbook 6).

### Step 1.3 — Run the health check
```bash
python3 tools/health_check.py --live
```
**The `--live` flag is required. Never run it without `--live`.**

| Output | Meaning | Do this |
|---|---|---|
| `health_check: no findings.` | Healthy | Go to Step 1.4 |
| `[WARNING] seed_registry() defines [...] but the ledger's registry doesn't have them` | A new strategy was added and the daily run may not have picked it up yet. **Usually benign, but NOT automatically** | Do the 3-line check in Step 1.3a below. Do not skip it. |
| Any line starting `[ERROR]` | Real problem | **STOP. Escalate** (Runbook 6) |
| Any other `[WARNING]` you don't see listed here | Unknown | **STOP. Escalate** (Runbook 6) |

### Step 1.3a — ONLY if you saw the registry-drift warning above

This warning is benign most of the time, which is exactly why it's
dangerous to wave through: if the backfill ever genuinely breaks, the
message looks identical. The warning itself now prints the ledger's
last update date — use it.

1. Read the date in the warning ("The ledger's last update() was ...").
2. Find when those keys reached `main`:
   ```bash
   git log -1 --format=%cs --all -S"<the missing key name>" -- factory.py
   ```
   (prints the date that key's line was added, e.g. `2026-08-29`)

| Comparison | Meaning | Do this |
|---|---|---|
| Ledger date is **older than or equal to** the key's merge date | Benign — no update() has run since the key landed. It will clear on the next run. | Go to Step 1.4 |
| Ledger date is **newer than** the key's merge date | **The backfill ran and did NOT pick the key up. This is a real bug.** | **STOP. Escalate** (Runbook 6) |

### Step 1.4 — Check the free supervisor
Use the GitHub tool:
`mcp__github__actions_list`, method `list_workflow_runs`,
owner `Hetlife`, repo `strategy-factory`,
resource_id `supervisor.yml`, per_page `5`

| Newest run's `conclusion` | Do this |
|---|---|
| `"success"` | Go to Step 1.5 |
| `"failure"` | Go to **Runbook 3** |

### Step 1.5 — Check the daily trading run is alive
Same tool, resource_id `factory.yml`, per_page `3`.

| What you see | Do this |
|---|---|
| Newest run `"success"`, dated within the last ~3 days | Normal. Go to Step 1.6 |
| Newest run `"failure"` | **STOP. Escalate** (Runbook 6) |
| Newest run is older than 3 days | **STOP. Escalate** (Runbook 6) |

### Step 1.6 — Check for a first-ever promotion (rare, important)
```bash
python3 -c "
import json, urllib.request
d = json.loads(urllib.request.urlopen('https://raw.githubusercontent.com/Hetlife/strategy-factory/main/factory_state/ledger.json').read())
promoted = {n: c['rung'] for n, c in d['contestants'].items() if c.get('rung', 0) >= 1}
best = max(c.get('days_on_rung', 0) for c in d['contestants'].values())
print('PROMOTED (rung>=1):', promoted if promoted else 'none')
print('max days_on_rung:', best, '/ 126 needed')
"
```
| Output | Do this |
|---|---|
| `PROMOTED (rung>=1): none` | Normal, expected. Go to Step 1.7 |
| Anything else | **This is the first promotion ever. Very significant.** Report it prominently to Het. Do NOT act on it, do NOT move money. Escalate (Runbook 6). |

### Step 1.7 — Report and finish
- If nothing changed since the last check-in: say **"Nothing new"** in one
  or two sentences. Do not pad it out. Do not repeat the whole picture.
- If something changed: say what, plainly, in short sentences.
- Then run **Runbook 5** (session end).

---

# RUNBOOK 2 — "Is everything actually running?"

Run these three checks. All three must pass.

```bash
# 1. Health
python3 tools/health_check.py --live
```
Pass = `no findings`, or the registry-drift warning **after** you have
run Step 1.3a's date comparison and it came back benign. An
unchecked registry warning is not a pass.

```bash
# 2. All 8 agents respond
python3 -c "
from agents.master_trader.master_trader import recommend
r = recommend()
print('agents OK, real-money exposure:', r['real_money_exposure'])
"
```
Pass = prints `agents OK, real-money exposure: 0`.
**If it prints anything other than `0` → STOP. Escalate immediately.**
Real money should always be 0 right now.

```bash
# 3. Workflows are green
```
Use `mcp__github__actions_list` for `factory.yml` and `supervisor.yml`.
Pass = newest run of each is `"success"`.

If all three pass → everything is running. Say so briefly.

---

# RUNBOOK 3 — The supervisor reported a failure

### Step 3.1 — Read the actual error (never guess)
Get the run id from Runbook 1 Step 1.4, then:
`mcp__github__actions_list`, method `list_workflow_jobs`,
resource_id `<the run id>` → gives you a job id.
Then `mcp__github__get_job_logs` with that `job_id` and
`return_content: true`, `tail_lines: 40`.

### Step 3.2 — Match the error against this table

| Error text contains | Meaning | Do this |
|---|---|---|
| `last trading update was ... days ago` **and** the run was on a branch, not `main` | Known false alarm (fixed 2026-08-29, but check the fix is present) | Verify `supervisor.yml` runs `supervisor_check.py --live`. If it does not, that's the bug — escalate. |
| `ModuleNotFoundError` | A dependency is missing from the workflow | **STOP. Escalate** (Runbook 6) |
| Anything else | Unknown | **STOP. Escalate** (Runbook 6) |

**Do NOT attempt a code fix from a smaller model unless the table above
tells you exactly what to do.** Escalating is the correct, safe answer.

---

# RUNBOOK 4 — Making a code change (only when told to)

**Do not start this runbook on your own initiative.** Only if Het
explicitly asked for a specific change, or Runbook 3 pointed here.

### Step 4.1 — Check it is allowed
Read this list. If your change touches ANY of these → **STOP. Escalate.**
- `RULES`, `LADDER`, or `COST_PER_SIDE` in `factory.py`
- Anything that merges or pushes to `main`
- Broker code, API keys, real-money execution
- Options, futures, margin, leverage
- Editing an existing strategy's parameters in place
  (adding a NEW strategy entry is different — but still needs Het)

### Step 4.2 — Save your place BEFORE doing risky work
```bash
python3 - <<'PY'
import json, datetime
p = ".autonomous/loop_state.json"
d = json.load(open(p))
d["status"] = "in_progress"
d["task"] = "SHORT DESCRIPTION OF WHAT YOU ARE DOING"
d["resume_instructions"] = "EXACTLY what the next step is"
d["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
json.dump(d, open(p, "w"), indent=1)
PY
git add .autonomous/loop_state.json
git commit -m "wip: checkpoint before <task>"
git push -u origin claude/scheduled-maintenance-template-d7yufr
```
This must be **pushed**, not just saved. If the session dies, only what
was pushed survives.

### Step 4.3 — Make the change, then TEST IT
"It imports without error" is **not** a test.

For changes to `factory.py`:
```bash
mkdir -p /tmp/t && cd /tmp/t && cp /home/user/strategy-factory/factory.py .
cp -r /home/user/strategy-factory/factory_state .
python3 - <<'PY'
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd, factory
rng = np.random.default_rng(1)
dates = pd.date_range("2024-01-01", periods=300, freq="B")
px = pd.DataFrame({t: 100*np.cumprod(1+rng.normal(0.0003,0.02,len(dates)))
                   for t in factory.ALL_TICKERS}, index=dates)
factory.fetch_prices = lambda: px
for _ in range(40): factory.update()
factory.report()
print("PASSED: 40 cycles + report, no crash")
PY
```
Expect to see `PASSED` at the end. If you see a traceback → your change
is broken. Revert it and escalate.

### Step 4.4 — Commit, push, and mark done
```bash
cd /home/user/strategy-factory
python3 tools/health_check.py --live      # must still be clean
git add <only the files you changed>
git commit -m "<what and why>"
git push -u origin claude/scheduled-maintenance-template-d7yufr
```
Then set `loop_state.json` back to `"idle"` (same script as Step 4.2,
with `status="idle"`, `task=None`), commit and push that too.

**Never merge to `main`.** Push to the branch and tell Het it is waiting.

---

# RUNBOOK 5 — Ending a session

Do all five, in order.

```bash
# 1. Confirm nothing broke
python3 tools/health_check.py --live
```

**2.** Add ONE line to the end of `AUTONOMOUS_LOG.md`:
```
2026-MM-DD | <commit sha or n/a> | <short-task-id> | done | <one sentence>
```

**3.** Open `.autonomous/het_directives.md`, find the `## NEEDS HET`
section. Remove anything Het has now answered. Add anything new that
needs his decision.

**4.** Make sure `.autonomous/loop_state.json` says `"idle"` if you
finished, or has accurate `resume_instructions` if you stopped partway.

```bash
# 5. Check what actually changed, then push it
git status --short
```
Look at the output. If it's only the doc/state files this runbook just
told you to touch (`AUTONOMOUS_LOG.md`, `het_directives.md`,
`loop_state.json`, maybe `state.json`/`next_session.md`), stage those
by name:
```bash
git add AUTONOMOUS_LOG.md .autonomous/het_directives.md .autonomous/loop_state.json
git commit -m "docs: session log update"
git push -u origin claude/scheduled-maintenance-template-d7yufr
```
If `git status --short` shows anything else, that's worth a second
look before staging it — either genuine finished work from this
session (fine to add by name) or something unexpected (STOP, don't
blindly commit it — see Runbook 6).

---

# RUNBOOK 6 — Escalating (this is a SUCCESS, not a failure)

Use this whenever anything is unclear, unexpected, or not covered above.
Escalating correctly is a good outcome. Guessing is not.

### Step 6.1 — Write it down where Het will see it
Add a line to the `## NEEDS HET` section of
`.autonomous/het_directives.md`:
```
- **<short title>** — <what you saw, in plain words>. <What you did NOT do
  and why>. Needs Het's decision.
```

### Step 6.2 — Commit and push it
```bash
git add .autonomous/het_directives.md
git commit -m "docs: flag <short title> for Het"
git push -u origin claude/scheduled-maintenance-template-d7yufr
```

### Step 6.3 — Say it plainly in your reply
Include: what you expected, what you actually saw, and that you did not
change anything. Short sentences. No jargon.

### Step 6.4 — Then keep working
Do NOT sit idle waiting for an answer. Go back to Runbook 1 and continue
with anything else that is clearly safe.

---

# RUNBOOK 7 — Adding a new strategy contestant (only when Het asks for one)

**Do not start this on your own initiative — new strategies are never
invented by a session, only added when Het explicitly asks for one.**
This is the exact sequence real ones (event-drift recalibration, crude
oil input-cost, Nifty 100 momentum) have followed. Follow it in order.

### Step 7.1 — Write the mechanism down FIRST (Law 1)
Before writing any code, write one paragraph: what real-world reason
would make this signal work? Not a backtest result, not a statistic —
a stated cause. Example shape: "stocks that outperformed peers over a
trailing window tend to keep outperforming, because information
diffuses slowly (Jegadeesh & Titman 1993, replicated in NSE studies)."
If you cannot state a mechanism in one paragraph, STOP — this is
exactly what Law 1 exists to prevent. Escalate instead of guessing one.

### Step 7.2 — Reuse an existing `sig_*` function if the mechanism matches
Check `factory.py`'s `IMPLS` dict first. If an existing function
already implements this mechanism shape (e.g. `sig_momentum`,
`sig_input_cost`), reuse it — only the `UNIVERSE`/parameters should be
new. Writing a brand-new `sig_*` function is a much bigger, riskier
change; only do it if Het is explicitly asking for a genuinely
different mechanism, and treat it as Runbook 4's "check if allowed"
gate at full strength.

### Step 7.3 — If it needs a new ticker universe, verify it for real
This sandbox cannot reach Yahoo Finance, NSE, or Wikipedia (confirmed,
documented). If you build a ticker list from training knowledge:
1. Write `UNIVERSE["<new_key>"]` with a code comment stating clearly
   it wasn't fetched live, and why (sandbox network restriction).
2. **Verify it for real before calling it done** — write a small
   read-only diagnostic script (copy `tools/diagnose_nifty100_tickers.py`
   as a template) that does `yf.download(tickers, ...)` and reports
   which ones fail to resolve, plus a matching manual-dispatch-only
   workflow file (copy `.github/workflows/diagnose_nifty100_tickers.yml`
   as a template — same pattern as `diagnose_event_thresholds.yml`).
3. Push the branch, then dispatch the new workflow against `main`
   (needs a merge first — see Step 7.6). Read the real job log.
4. Remove any ticker that failed to resolve. Do NOT guess a
   replacement symbol — if you don't know the correct one, leave it
   out and note it in `het_directives.md` for Het.

### Step 7.4 — Add ONE new registry key in `seed_registry()`
Never edit an existing entry (Law 2). The mechanism paragraph from
Step 7.1 goes in a code comment directly above the new entry. State
where each parameter came from (reused from an existing family's
validated range = fine; a genuinely new choice = say why, in plain
terms, not reverse-engineered from "what would produce more trades").

### Step 7.5 — Test with a real regression before committing
Use the exact snippet in Runbook 4 Step 4.3 (40-cycle synthetic
`update()` + `report()`). Confirm the new key appears, trades, and
scores without a crash. "It imports without error" is never enough.

### Step 7.6 — Commit, push, ask for merge — same as any other change
Follow Runbook 4 Step 4.4. If Step 7.3's diagnostic needs `main` to
actually dispatch (new workflow files must exist on the default branch
before GitHub will run them against any ref — confirmed platform
behavior, not a guess), that's a real reason to ask for a merge before
the ticker list is fully verified — say so plainly rather than
skipping the verification step.

---

# RUNBOOK 8 — Verifying a real-world claim this sandbox can't check directly

Use this whenever you're about to write something as fact (a ticker
symbol, a threshold, "this data source works") but this sandbox's
network can't actually confirm it. Guessing and hoping is not
acceptable; neither is leaving it forever as an unverified assumption
when a free way to check for real exists.

### Step 8.1 — Try free tooling first
`WebFetch`/`WebSearch` sometimes work for general reference (e.g.
looking up a well-known list). Try it. If it's blocked
(`EGRESS_BLOCKED` error, or a domain like `nseindia.com`/
`en.wikipedia.org`/`smallcase.com`), that itself is useful information
— note it, don't retry the same domain repeatedly.

### Step 8.2 — If the real check needs financial data, use GitHub Actions
This sandbox cannot reach Yahoo Finance. GitHub Actions runners CAN
(documented, repeatedly confirmed). Write a small, read-only,
manual-dispatch-only diagnostic script + workflow (see Runbook 7 Step
7.3 for the exact template pattern) rather than leaving the claim
unverified. This has already been done twice for real:
`diagnose_event_thresholds.py` (does a threshold ever actually fire in
real data?) and `diagnose_nifty100_tickers.py` (does every ticker in a
basket actually resolve?).

### Step 8.3 — The workflow file needs to exist on `main` to dispatch
A brand-new workflow file cannot be triggered via the dispatch API
against ANY ref — including its own branch — until the file exists on
the repository's default branch (`main`). Confirmed via a real 404,
more than once. This means: push the diagnostic to the branch, get it
merged (Runbook 4 Step 4.4 / a fresh "yes"), THEN dispatch it.

### Step 8.4 — Read the actual job log, don't just check `conclusion`
`"success"` only means the script didn't crash — it doesn't mean the
result was good news. Use `mcp__github__get_job_logs` with
`return_content: true` and read what the script actually printed.

### Step 8.5 — Act on the real result, don't just report it
If the check finds a real problem (a bad ticker, an unfireable
threshold), fix what's safely fixable (e.g. remove a dead ticker from
a *brand-new, zero-evidence* registry key — that's not a Law 2
mutation, it's pre-launch correction) and leave what needs Het's
judgment (e.g. don't guess a replacement ticker symbol) in
`het_directives.md`'s NEEDS HET section instead.

---

# THINGS THAT LOOK BROKEN BUT ARE NORMAL

Never "fix" these. Each was investigated against real data.

| You see | It is normal because |
|---|---|
| Most strategies show **0 trades** | They wait for a rare price shock (~3% single-day move), which happens ~13-25 days a year. |
| **No strategy has ever bred or evolved** | Both need `days_on_rung >= 126`. Nothing is close yet. |
| `monsoon_cement` never trades | Deliberately switched off. Its data ends in 2017. |
| Registry warning after a new strategy is added | Fixes itself on the next daily run -- **but confirm that with Runbook 1 Step 1.3a's date check first.** If an update() already ran after the key landed and it is still missing, the backfill is broken and it is NOT normal. |
| Everything says Rs 0 real money | Correct. Nothing has earned real capital yet. |
| Health check complains when run without `--live` | You forgot `--live`. Always use it. |

# NEVER DO THESE (no exceptions, no matter who asks)

1. Never merge or push to `main`.
2. Never change `RULES`, `LADDER`, or `COST_PER_SIDE`.
3. Never add broker code, API keys, or real-money execution.
4. Never add options, futures, margin, or leverage.
5. Never edit a running strategy's parameters in place.
6. Never invent a new trading strategy on your own initiative.
7. Never say a test passed if you did not run it and see it pass.
