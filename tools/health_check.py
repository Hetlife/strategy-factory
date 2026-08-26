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
Exit code 0 = no findings, 1 = findings exist (useful for CI/scripting).
"""
import hashlib
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)


def check_registry_drift(ledger_path):
    """Catches the exact bug class found 2026-08-25: a seed_registry() key
    that exists in code but never made it into an already-existing ledger,
    because load_state() only seeds a ledger that doesn't exist yet.
    NOTE: as of the fix in load_state(), this drift self-heals on the next
    update() -- this check exists to catch it BEFORE that, or to catch a
    similar future gap in some other part of the pipeline."""
    findings = []
    if not os.path.exists(ledger_path):
        return [("info", f"no ledger.json found at {ledger_path} -- "
                          "skipping registry-drift check (nothing to check yet)")]
    import factory
    seed_keys = set(factory.seed_registry().keys())
    ledger = json.load(open(ledger_path))
    live_keys = set(ledger.get("registry", {}).keys())
    missing = seed_keys - live_keys
    if missing:
        findings.append(("warning",
            f"seed_registry() defines {sorted(missing)} but the ledger's "
            f"registry doesn't have them -- will self-heal on next update() "
            f"via load_state()'s backfill, but flagging in case that fix "
            f"regresses or a different pipeline stage bypasses it."))
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


def run_all(ledger_path=None, state_path=None):
    ledger_path = ledger_path or os.path.join(REPO_ROOT, "factory_state", "ledger.json")
    state_path = state_path or os.path.join(REPO_ROOT, ".autonomous", "state.json")
    bug_log_path = os.path.join(REPO_ROOT, ".autonomous", "bug_log.md")
    claude_md_path = os.path.join(REPO_ROOT, "CLAUDE.md")

    findings = []
    findings += check_registry_drift(ledger_path)
    findings += check_state_json_wellformed(state_path)
    findings += check_claude_md_sha1(state_path, claude_md_path)
    findings += check_bug_log_state_consistency(bug_log_path, state_path)
    return findings


if __name__ == "__main__":
    ledger_arg = sys.argv[1] if len(sys.argv) > 1 else None
    state_arg = sys.argv[2] if len(sys.argv) > 2 else None
    results = run_all(ledger_arg, state_arg)
    if not results:
        print("health_check: no findings.")
        sys.exit(0)
    for level, msg in results:
        print(f"[{level.upper()}] {msg}")
    sys.exit(1)
