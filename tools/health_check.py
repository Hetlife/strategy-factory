"""
STRATEGY FACTORY - deterministic repo health check
====================================================
Purpose: replace repeated ad-hoc reasoning (a session manually re-deriving
"is the ledger missing anything, does state.json agree with itself") with
a single script that answers those exact questions every time, the same
way, for free. This exists because of a real incident: P0-3's
nifty_benchmark contestant sat merged in code but silently absent from
the live ledger for a full day before anyone happened to check by hand.
A script like this, run routinely, would have caught it on day one instead.

Every check here is PURE CODE -- no LLM judgment required to run it. A
session (interactive or Routine-fired) should run this FIRST, before
spending any tokens manually re-deriving the same facts via file reads.
Findings still need a human or an LLM session to decide what to DO about
them -- this script only detects, never fixes.

USAGE:  python tools/health_check.py [path/to/ledger.json] [path/to/state.json]
        python tools/health_check.py --live
Exit code 0 = no findings, 1 = findings exist (useful for CI/scripting).

--live fetches factory_state/ledger.json and .autonomous/state.json fresh
from main's raw GitHub content instead of reading the local checkout.
Added 2026-08-26 after a real recurring mistake: an interactive session's
local checkout tracks the WORKING BRANCH, but ledger.json is updated only
on main by factory.yml's daily cron -- so a plain local run here reliably
reports a stale/false "registry drift" warning that isn't real on main.
Every Routine prompt already says "fetch fresh, don't trust a stale local
copy" in English each time; this flag does that fetch in code instead, so
it stops needing to be re-said (and re-forgotten) every firing.
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

RAW_BASE = "https://raw.githubusercontent.com/Hetlife/strategy-factory/main"


def fetch_live_json(repo_relative_path, timeout=15):
    """Fetches a file fresh from main via GitHub raw content. Returns the
    parsed JSON, or raises with a clear message on any failure (network,
    404, bad JSON) rather than letting a session guess at a stack trace."""
    url = f"{RAW_BASE}/{repo_relative_path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        raise RuntimeError(
            f"--live fetch failed for {url}: {e}. Falling back to a local "
            f"path won't give a trustworthy answer for this check -- fix "
            f"the network issue or fall back to explicit local paths "
            f"knowing they may be stale.") from e


def _ledger_last_update_date(ledger_data):
    """Newest date recorded in any contestant's history -- i.e. the last day
    an update() run actually executed and committed. ledger.json has no
    top-level timestamp, so contestant history is the honest source for
    this. Returns None if nothing dated is present (a brand-new ledger, or
    a malformed one) -- callers must handle that rather than assume a date.
    Deliberately tolerant of odd/short history rows: a monitoring helper
    must never be the thing that raises."""
    dates = []
    for c in (ledger_data.get("contestants") or {}).values():
        if not isinstance(c, dict):
            continue
        hist = c.get("history") or []
        if not hist:
            continue
        row = hist[-1]
        if isinstance(row, (list, tuple)) and row:
            dates.append(str(row[0]))
        elif isinstance(row, dict) and row.get("date"):
            dates.append(str(row["date"]))
    return max(dates) if dates else None


def check_registry_drift(ledger_path=None, ledger_data=None):
    """Catches the exact bug class found 2026-08-25: a seed_registry() key
    that exists in code but never made it into an already-existing ledger,
    because load_state() only seeds a ledger that doesn't exist yet.
    NOTE: as of the fix in load_state(), this drift self-heals on the next
    update() -- this check exists to catch it BEFORE that, or to catch a
    similar future gap in some other part of the pipeline.

    Pass ledger_data (an already-loaded dict, e.g. from --live) to skip the
    local-file read entirely -- see fetch_live_json()."""
    findings = []
    if ledger_data is None:
        if not os.path.exists(ledger_path):
            return [("info", f"no ledger.json found at {ledger_path} -- "
                              "skipping registry-drift check (nothing to check yet)")]
        ledger_data = json.load(open(ledger_path))
    import factory
    seed_keys = set(factory.seed_registry().keys())
    ledger = ledger_data
    live_keys = set(ledger.get("registry", {}).keys())
    missing = seed_keys - live_keys
    if missing:
        last = _ledger_last_update_date(ledger_data)
        if last:
            detail = (
                f"The ledger's last update() was {last}. BENIGN if that date "
                f"is BEFORE these keys reached main -- load_state() backfills "
                f"them on the next update() run, so it clears itself. A REAL "
                f"BUG if an update() has run since they reached main and they "
                f"are STILL missing, because that means the backfill silently "
                f"failed. To tell which: compare {last} against the date those "
                f"keys were merged to main. Do not reflexively dismiss this "
                f"without doing that check.")
        else:
            detail = (
                "The ledger has no dated contestant history, so this check "
                "cannot tell whether an update() has run since these keys "
                "reached main. That is itself unusual for a ledger that has "
                "been trading -- treat an undated ledger as worth a human "
                "look rather than assuming the drift is benign.")
        findings.append(("warning",
            f"seed_registry() defines {sorted(missing)} but the ledger's "
            f"registry doesn't have them. {detail}"))
    orphans = live_keys - seed_keys
    # orphans are EXPECTED (bred/evolved children aren't in seed_registry) --
    # only flag if something looks like a seed-style name with no lineage,
    # which would suggest an actual naming mismatch rather than a real child.
    contestants = ledger.get("contestants", {})
    for name in sorted(orphans):
        c = contestants.get(name, {})
        if c and not c.get("lineage"):
            findings.append(("info",
                f"'{name}' is in the ledger's registry/contestants but not "
                f"in current seed_registry(), and has no lineage recorded -- "
                f"probably just an older seed name that was since removed "
                f"from seed_registry(), not necessarily a bug. Worth a human "
                f"glance if it's unexpected."))
    return findings


def check_state_json_wellformed(state_path):
    findings = []
    if not os.path.exists(state_path):
        return [("error", f"state.json not found at {state_path}")]
    state = json.load(open(state_path))
    for item in state.get("queue", []):
        for required in ("id", "priority", "status", "summary"):
            if required not in item:
                findings.append(("error",
                    f"queue item missing required field '{required}': "
                    f"{item.get('id', '<no id>')}"))
        commit = item.get("commit", "")
        if commit and not re.match(r"^([0-9a-f]{7,40}|n/a.*)$", commit):
            findings.append(("warning",
                f"queue item '{item.get('id')}' has a commit field that "
                f"doesn't look like a real sha or an explicit n/a-* tag: "
                f"'{commit}' -- possibly a typo."))
    return findings


def check_claude_md_sha1(state_path, claude_md_path):
    findings = []
    if not (os.path.exists(state_path) and os.path.exists(claude_md_path)):
        return findings
    state = json.load(open(state_path))
    recorded = state.get("claude_md_sha1", "")
    actual = hashlib.sha1(open(claude_md_path, "rb").read()).hexdigest()
    # historical entries in this project have sometimes carried one stray
    # leading/trailing char -- compare on the real 40-char hex substring.
    recorded_clean = re.sub(r"[^0-9a-f]", "", recorded)[-40:]
    if recorded_clean != actual:
        findings.append(("warning",
            f"state.json's claude_md_sha1 ({recorded}) doesn't match "
            f"CLAUDE.md's actual sha1 ({actual}) -- CLAUDE.md was edited "
            f"without updating the recorded hash, or vice versa."))
    return findings


def check_bug_log_state_consistency(bug_log_path, state_path):
    """Lightweight heuristic: an id that state.json's queue marks as
    done/closed/cleared shouldn't still appear under bug_log.md's OPEN
    section header. String-matching, not semantic -- false negatives are
    expected and fine, this is a cheap tripwire, not a proof."""
    findings = []
    if not (os.path.exists(bug_log_path) and os.path.exists(state_path)):
        return findings
    state = json.load(open(state_path))
    resolved_ids = {
        item["id"] for item in state.get("queue", [])
        if any(tag in item.get("status", "")
               for tag in ("done", "cleared", "closed", "fixed"))
    }
    text = open(bug_log_path).read()
    open_section = text.split("## FIXED")[0] if "## FIXED" in text else text
    for rid in resolved_ids:
        # only meaningful for ids that look like they'd appear verbatim
        if rid in open_section and "## OPEN" in open_section:
            # allow it if that exact line is also tagged CLOSED/FIXED nearby
            idx = open_section.find(rid)
            nearby = open_section[max(0, idx - 80):idx]
            if "CLOSED" not in nearby and "FIXED" not in nearby:
                findings.append(("info",
                    f"state.json marks '{rid}' as resolved, but bug_log.md's "
                    f"OPEN section still mentions it without a CLOSED/FIXED "
                    f"tag nearby -- worth a human glance, may just be a "
                    f"historical mention, not a real contradiction."))
    return findings


def run_all(ledger_path=None, state_path=None, live=False):
    ledger_path = ledger_path or os.path.join(REPO_ROOT, "factory_state", "ledger.json")
    state_path = state_path or os.path.join(REPO_ROOT, ".autonomous", "state.json")
    bug_log_path = os.path.join(REPO_ROOT, ".autonomous", "bug_log.md")
    claude_md_path = os.path.join(REPO_ROOT, "CLAUDE.md")

    findings = []
    if live:
        ledger_data = fetch_live_json("factory_state/ledger.json")
        findings += check_registry_drift(ledger_data=ledger_data)
    else:
        findings += check_registry_drift(ledger_path=ledger_path)
    # state.json/CLAUDE.md/bug_log.md aren't subject to the same
    # branch-vs-main drift (they're not written by factory.yml's
    # main-only cron) -- local checkout is a trustworthy source for these
    # regardless of --live.
    findings += check_state_json_wellformed(state_path)
    findings += check_claude_md_sha1(state_path, claude_md_path)
    findings += check_bug_log_state_consistency(bug_log_path, state_path)
    return findings


if __name__ == "__main__":
    args = sys.argv[1:]
    live_mode = "--live" in args
    if live_mode:
        args = [a for a in args if a != "--live"]
        print("health_check: --live mode, fetching factory_state/ledger.json fresh from main...")
    ledger_arg = args[0] if len(args) > 0 else None
    state_arg = args[1] if len(args) > 1 else None
    try:
        results = run_all(ledger_arg, state_arg, live=live_mode)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    if not results:
        print("health_check: no findings.")
        sys.exit(0)
    for level, msg in results:
        print(f"[{level.upper()}] {msg}")
    sys.exit(1)
