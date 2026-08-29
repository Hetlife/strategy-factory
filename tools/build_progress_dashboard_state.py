"""
Generates the data snapshot for the "Progress" Artifact -- a clean,
Apple-style view of real project activity (AUTONOMOUS_LOG.md, live
ledger stats), separate from the pixel-art Trading Floor artifact and
the Streamlit P&L dashboard. Same snapshot-at-publish-time pattern as
tools/build_trading_floor_state.py (Artifact CSP blocks client-side
cross-origin fetch, so this bakes real data in at publish time instead
of leaving the page to fetch live).

Read-only. Never writes to ledger.json/state.json/seed_registry().

Published at https://claude.ai/code/artifact/e16ae3c5-4ec1-4ef3-8334-d2cf28e82989
(2026-08-29). The HTML/CSS/JS page itself is NOT committed to this repo
-- same convention as the Trading Floor artifact (only its data-builder
script lives here). To update the page: `Artifact({action:"read",
url:...})` to pull the current published source, re-run this script for
a fresh JSON snapshot, splice it into the <script id="progress-data">
tag, then republish to the same URL. Categorization/status heuristics
below (categorize(), status()) are read by that page's JS via the
"category"/"status" fields on each entry -- keep them in sync if you
change the labels/colors client-side.

USAGE: python tools/build_progress_dashboard_state.py > /path/to/out.json
"""
import json
import re
import sys
import os
import urllib.request
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)


def parse_log(path):
    entries = []
    for line in open(path):
        line = line.rstrip("\n")
        if not re.match(r"^\d{4}-\d{2}-\d{2}", line):
            continue
        parts = line.split(" | ", 4)
        if len(parts) != 5:
            continue
        date, commit, qid, outcome, note = parts
        entries.append({
            "date": date.strip(), "commit": commit.strip(), "id": qid.strip(),
            "outcome": outcome.strip(), "note": note.strip(),
        })
    return entries


def categorize(e):
    idl = e["id"].lower()
    if "merge" in idl:
        return "merge"
    if "fix" in idl:
        return "fix"
    if "diag" in idl:
        return "diagnostic"
    if any(k in idl for k in ("contestant", "sync", "checkpoint-procedure", "cache", "backfill")):
        return "feature"
    return "docs"


def status(e):
    o = e["outcome"].lower()
    if "unmerged" in o or "on branch" in o or "not merged" in o:
        return "pending"
    if o.startswith("done"):
        return "done"
    return "info"


def fetch_live_json(path):
    url = f"https://raw.githubusercontent.com/Hetlife/strategy-factory/main/{path}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read())


def main():
    entries = parse_log(os.path.join(REPO_ROOT, "AUTONOMOUS_LOG.md"))
    for e in entries:
        e["category"] = categorize(e)
        e["status"] = status(e)

    by_day = {}
    for e in entries:
        by_day.setdefault(e["date"], []).append(e)
    days = [{"date": d, "entries": list(reversed(es))}
             for d, es in sorted(by_day.items(), reverse=True)]

    stats = {"health": "unknown", "days_on_rung": None, "days_needed": 126,
              "contestants": None, "retired": 0, "open_items": None}
    try:
        ledger = fetch_live_json("factory_state/ledger.json")
        contestants = ledger.get("contestants", {})
        stats["contestants"] = len(contestants)
        stats["retired"] = sum(1 for c in contestants.values() if c.get("retired"))
        stats["days_on_rung"] = max((c.get("days_on_rung", 0) for c in contestants.values()), default=0)
    except Exception as exc:
        stats["fetch_error"] = str(exc)

    try:
        state = fetch_live_json(".autonomous/state.json")
        stats["open_items"] = sum(
            1 for q in state.get("queue", [])
            if "done" not in q.get("status", "") and "blocked" not in q.get("status", "")
            and "watch" not in q.get("status", "") and "gated" not in q.get("status", "")
            and "out_of_scope" not in q.get("status", "")
        )
    except Exception:
        pass

    try:
        import subprocess
        r = subprocess.run(["python3", "tools/health_check.py", "--live"],
                            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
        out = r.stdout + r.stderr
        if "no findings" in out:
            stats["health"] = "clean"
        elif "[ERROR]" in out:
            stats["health"] = "error"
        elif "[WARNING]" in out:
            stats["health"] = "warning"
    except Exception:
        pass

    counts = Counter(e["category"] for e in entries)

    output = {
        "generated_at": None,
        "stats": stats,
        "category_counts": dict(counts),
        "total_entries": len(entries),
        "days": days,
    }
    print(json.dumps(output, indent=1))


if __name__ == "__main__":
    main()
