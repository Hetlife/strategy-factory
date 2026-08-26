"""
Builds the JSON snapshot embedded in the "Trading Floor" Artifact
(agent grid, uptime, leaderboard, recent activity, open questions) from
real repo data -- no hand-typing agent lists or log entries into a
throwaway Python script each time the page needs a refresh.

Origin: Het, 2026-08-26, asked for "programs and files to make the
repeat work easier." Building/publishing the artifact had involved
manually retyping the agent roster, best/worst performer, and recent
log entries into an inline script three separate times this session --
repetitive and error-prone (a hand-typed number or missed new agent is
exactly the kind of drift health_check.py exists to catch elsewhere).
This does it from the real files instead, every time.

Auto-discovers agents from agents/*/*.py (so a future HR hire shows up
here with zero manual edits), reads real git last-touched dates, real
ledger.json equities for the leaderboard, and real AUTONOMOUS_LOG.md /
het_directives.md content for the activity feed and open questions.

USAGE:
    python3 tools/build_trading_floor_state.py [output_path]
    (default output: <repo>/factory_state/trading_floor_state.json --
    NOT committed/read by any trading logic, purely a build artifact for
    republishing the Artifact page by hand)
"""
import datetime
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

STALE_DAYS_THRESHOLD = 3
LOG_ENTRY_LIMIT = 8
NOTE_MAX_CHARS = 160


def _git_last_touched(path):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def discover_agents():
    agents_dir = os.path.join(REPO_ROOT, "agents")
    agents = []
    today = datetime.date.today()
    for name in sorted(os.listdir(agents_dir)):
        role_dir = os.path.join(agents_dir, name)
        py_path = os.path.join(role_dir, f"{name}.py")
        if not os.path.isfile(py_path):
            continue
        text = open(py_path).read()
        m = re.search(r'"""(.+?) agent -- (.+?)(?:\n\n|""")', text, re.S)
        role = m.group(2).strip() if m else "No description yet."
        role = re.sub(r"\s+", " ", role)  # collapse wrapped-line whitespace
        if len(role) > 180:
            role = role.rsplit(" ", 1)[0].rstrip(",.;") + "..."
        touched = _git_last_touched(py_path) or today.isoformat()
        days_ago = (today - datetime.date.fromisoformat(touched)).days
        agents.append({
            "id": name,
            "name": _NAME_OVERRIDES.get(name, name.replace("_", " ").title()),
            "icon": _ICONS.get(name, "🧩"),
            "role": role,
            "file": f"agents/{name}/{name}.py",
            "touched": touched,
            "daysAgo": days_ago,
            "status": "active" if days_ago <= STALE_DAYS_THRESHOLD else "idle",
            "url": f"https://github.com/Hetlife/strategy-factory/blob/main/agents/{name}/{name}.py",
        })
    return agents


_ICONS = {
    "judge": "⚖️", "researcher": "🔬", "breeder": "🧬", "risk_manager": "🛡️",
    "reporter": "📣", "healer": "🩹", "hr": "🗂️",
}
_NAME_OVERRIDES = {"hr": "HR"}


def leaderboard(ledger):
    live = {n: s for n, s in ledger.get("contestants", {}).items()
            if not s.get("retired")}
    if not live:
        return None, None
    best_name = max(live, key=lambda n: live[n].get("equity", 1.0))
    worst_name = min(live, key=lambda n: live[n].get("equity", 1.0))
    return (
        {"name": best_name, "equity": live[best_name].get("equity", 1.0)},
        {"name": worst_name, "equity": live[worst_name].get("equity", 1.0)},
    )


def recent_log_entries(path, limit=LOG_ENTRY_LIMIT):
    if not os.path.exists(path):
        return []
    lines = [l for l in open(path).read().strip().splitlines()
             if re.match(r"^\d{4}-\d{2}-\d{2} \|", l)]
    entries = []
    for line in lines[-limit:]:
        parts = [p.strip() for p in line.split("|", 4)]
        if len(parts) < 5:
            continue
        date, _commit, qid, outcome, note = parts
        if len(note) > NOTE_MAX_CHARS:
            note = note[:NOTE_MAX_CHARS - 3] + "..."
        entries.append({"date": date, "id": qid, "outcome": outcome, "note": note})
    return entries


def open_questions(path):
    if not os.path.exists(path):
        return []
    text = open(path).read()
    if "## NEEDS HET" not in text:
        return []
    section = text.split("## NEEDS HET", 1)[1]
    qs = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        item = re.sub(r"^- ", "", line)
        # Skip pure status notes (no actual open question/decision for Het).
        if re.search(r"^(No open|Het is away)", item):
            continue
        if len(item) > 220:
            item = item[:217] + "..."
        qs.append(item)
    return qs


def build(ledger_path=None, state_path=None, log_path=None, directives_path=None):
    ledger_path = ledger_path or os.path.join(REPO_ROOT, "factory_state", "ledger.json")
    state_path = state_path or os.path.join(REPO_ROOT, ".autonomous", "state.json")
    log_path = log_path or os.path.join(REPO_ROOT, "AUTONOMOUS_LOG.md")
    directives_path = directives_path or os.path.join(REPO_ROOT, ".autonomous", "het_directives.md")

    ledger = json.load(open(ledger_path)) if os.path.exists(ledger_path) else {"contestants": {}}

    from tools import health_check
    findings = health_check.run_all(ledger_path, state_path) if os.path.exists(state_path) else []
    errors = [f for f in findings if f[0] == "error"]
    real = [f for f in findings if f[0] != "info"]
    level = "error" if errors else ("warn" if real else "good")

    dates = [s["history"][-1][0] for s in ledger.get("contestants", {}).values() if s.get("history")]
    last_update = max(dates) if dates else None
    stale_days = None
    online = True
    if last_update:
        stale_days = (datetime.date.today() - datetime.date.fromisoformat(last_update)).days
        online = stale_days <= STALE_DAYS_THRESHOLD
    if level == "error":
        online = False

    con = ledger.get("contestants", {})
    active_n = sum(1 for s in con.values() if not s.get("retired"))
    best, worst = leaderboard(ledger)

    state_json = json.load(open(state_path)) if os.path.exists(state_path) else {}
    phase = {"phase_0": "Phase 0 -- infra gate", "phase_1": "Phase 1 -- paper trading, evidence window"}.get(
        state_json.get("current_phase"), state_json.get("current_phase", "unknown phase"))

    out = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": phase,
        "lastTradingUpdate": last_update,
        "staleDays": stale_days,
        "online": online,
        "health": {"level": level, "findings": [msg for _, msg in real]},
        "contestants": {"total": len(con), "active": active_n, "retired": len(con) - active_n},
        "best": best,
        "worst": worst,
        "agents": discover_agents(),
        "needsHet": open_questions(directives_path),
        "log": recent_log_entries(log_path),
        "notes": [],
    }
    return out


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        REPO_ROOT, "factory_state", "trading_floor_state.json")
    state = build()
    with open(out_path, "w") as f:
        json.dump(state, f, indent=None, separators=(",", ":"))
    print(f"Wrote {out_path}")
    print(f"  {len(state['agents'])} agents, {len(state['log'])} log entries, "
          f"{len(state['needsHet'])} open question(s), online={state['online']}")
