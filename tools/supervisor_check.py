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


def check_pipeline_staleness(ledger_path, ledger_data=None):
    """Pass ledger_data (already loaded, e.g. fetched live from main) to skip
    the local-file read.

    Why that matters: `ledger.json` is ONLY ever auto-committed to `main` by
    factory.yml -- never to a feature branch. So reading the local checkout's
    copy while on a branch reports a days-stale ledger that is perfectly
    fresh on main, and this function turns that into an ERROR reading "the
    daily factory.yml run may have stopped firing." That is the single most
    alarming thing this script can say, and it was firing falsely: caught
    2026-08-29 by dispatching supervisor.yml against the feature branch,
    which failed the job with exactly that message while the daily run was
    in fact healthy and had committed the day before. Same root cause as the
    health_check.py stale-checkout false positive fixed earlier. A monitor
    that cries wolf on its own headline alarm trains everyone to ignore it,
    so the workflow now always runs with --live."""
    if ledger_data is None:
        if not os.path.exists(ledger_path):
            return [("error", f"no ledger.json found at {ledger_path} -- "
                     "the daily pipeline has never produced one, or it's missing.")]
        with open(ledger_path) as f:
            ledger_data = json.load(f)
    ledger = ledger_data
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
    live = "--live" in sys.argv[1:]
    ledger_path = os.path.join(REPO_ROOT, "factory_state", "ledger.json")
    state_path = os.path.join(REPO_ROOT, ".autonomous", "state.json")

    ledger_data = None
    if live:
        print("supervisor_check: --live mode, fetching ledger.json fresh from main...")
        try:
            ledger_data = health_check.fetch_live_json("factory_state/ledger.json")
        except RuntimeError as e:
            # A failed fetch must NOT be silently downgraded to reading the
            # stale local copy -- that reintroduces exactly the false
            # "pipeline stopped firing" alarm this flag exists to prevent.
            print(f"[ERROR] {e}")
            sys.exit(2)

    findings = health_check.run_all(ledger_path, state_path, live=live)
    findings += check_pipeline_staleness(ledger_path, ledger_data=ledger_data)

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
