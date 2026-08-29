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
judgment), `CLAUDE.md` (binding rules — always wins over this file).

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
| `[WARNING] seed_registry() defines [...] but the ledger's registry doesn't have them` | Normal, self-healing. A new strategy was added and the daily run hasn't picked it up yet. | Ignore. Go to Step 1.4 |
| Any line starting `[ERROR]` | Real problem | **STOP. Escalate** (Runbook 6) |
| Any other `[WARNING]` you don't see listed here | Unknown | **STOP. Escalate** (Runbook 6) |

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
Pass = `no findings`, or only the known self-healing registry warning.

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
# 5. Push everything
git add -A && git commit -m "docs: session log update"
git push -u origin claude/scheduled-maintenance-template-d7yufr
```

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

# THINGS THAT LOOK BROKEN BUT ARE NORMAL

Never "fix" these. Each was investigated against real data.

| You see | It is normal because |
|---|---|
| Most strategies show **0 trades** | They wait for a rare price shock (~3% single-day move), which happens ~13-25 days a year. |
| **No strategy has ever bred or evolved** | Both need `days_on_rung >= 126`. Nothing is close yet. |
| `monsoon_cement` never trades | Deliberately switched off. Its data ends in 2017. |
| Registry warning after a new strategy is added | Fixes itself on the next daily run. |
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
