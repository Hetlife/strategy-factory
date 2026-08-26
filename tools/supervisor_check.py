"""Supervisor: a code-only, zero-token check-in on the whole pipeline,
run every ~15 min by .github/workflows/supervisor.yml (GitHub Actions'
own free minutes -- no Claude session, no extra cost per Het's explicit
"ask before there's any cost involved" constraint).

Deliberately NOT a Claude session. The underlying data (trades, prices)
only changes once per weekday, so a 15-min cadence exists to catch the
pipeline actually breaking, not to re-derive anything -- pure code is the
right tool, same "code over tokens" reasoning as tools/health_check.py.

Two things it checks:
  1. Runs tools/health_check.py's existing repo-consistency checks, but
     only FAILS the job on an "error"-level finding. "warning"/"info"
     findings (like a registry entry that's about to self-heal on the
     next scheduled update()) print but don't turn the run red -- a
     supervisor that cries wolf on expected, self-healing states trains
     everyone to ignore it.
  2. Checks whether the daily factory.yml pipeline has actually gone
     stale (no ledger update in >3 days) -- the one thing worth a real
     red X: the automation quietly stopped.

Exit code 0 = nothing worth a human's attention. Exit code 1 = something
is. Never writes/commits anything -- detection only, same as every other
agent in agents/.
"""
import datetime
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from tools import health_check

STALE_DAYS_THRESHOLD = 3


def check_pipeline_staleness(ledger_path):
    if not os.path.exists(ledger_path):
        return [("error", f"no ledger.json found at {ledger_path} -- "
                 "the daily pipeline has never produced one, or it's missing.")]
    with open(ledger_path) as f:
        ledger = json.load(f)
    dates = [s["history"][-1][0] for s in ledger.get("contestants", {}).values()
             if s.get("history")]
    if not dates:
        return [("warning", "ledger.json exists but no contestant has any "
                 "trading history yet.")]
    last = max(dates)
    days_stale = (datetime.datetime.now(datetime.timezone.utc).date()
                  - datetime.date(*map(int, last.split("-")))).days
    if days_stale > STALE_DAYS_THRESHOLD:
        return [("error", f"last trading update was {last}, {days_stale} days "
                 f"ago -- more than a long weekend. The daily factory.yml run "
                 f"may have stopped firing.")]
    return [("info", f"last trading update {last} ({days_stale}d ago) -- fine.")]


def main():
    ledger_path = os.path.join(REPO_ROOT, "factory_state", "ledger.json")
    state_path = os.path.join(REPO_ROOT, ".autonomous", "state.json")

    findings = health_check.run_all(ledger_path, state_path)
    findings += check_pipeline_staleness(ledger_path)

    errors = [f for f in findings if f[0] == "error"]
    others = [f for f in findings if f[0] != "error"]

    for level, msg in findings:
        print(f"[{level.upper()}] {msg}")

    if errors:
        print(f"\nSUPERVISOR: {len(errors)} error-level finding(s) -- failing the run.")
        sys.exit(1)

    print(f"\nSUPERVISOR: all clear ({len(others)} informational finding(s), "
          "nothing that needs a human).")
    sys.exit(0)


if __name__ == "__main__":
    main()
