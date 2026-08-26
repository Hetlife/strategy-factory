"""
HR agent -- scaffolds new team-role helper agents (Judge/Researcher/Breeder/
Risk Manager/Reporter/Healer-style tooling), never trading strategies.

Origin: Het, 2026-08-26, asked for an agent that can "hire more sub agents
for each main agent and even hire main agents." Clarified with him directly
before building (AskUserQuestion): "main agents" means the existing
agents/ team roles (tooling), NOT trading strategy contestants -- this
stays completely outside factory.py's registry/Law 1 territory, same as
every other agent here. He also confirmed the first 10 hires can be built
on Claude's own judgment (matching existing safe patterns, free, code-only)
without asking him each time; 11+ needs his sign-off.

Unlike the other agents (read-only/advisory), this one DOES create files --
but only ever new agents/<role>/ scaffolding, and only when a session
deliberately calls scaffold_agent() after judging a real gap exists (the
same "code over tokens" bar that produced healer.py: a session noticing it
keeps re-deriving the same thing by hand). It never runs unsupervised and
never invents a hire just to use the allowance -- see .autonomous/hr_log.md
for the running count and the reasoning behind every hire so far.

USAGE:
    from agents.hr.hr import propose_hire, scaffold_agent, hire_count
"""
import datetime
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

HR_LOG_PATH = os.path.join(REPO_ROOT, ".autonomous", "hr_log.md")
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")
PRE_AUTHORIZED_HIRES = 10

# Defense-in-depth, not the only guard: a hire whose name/description reads
# like it's about generating trading signals gets refused outright, even
# though the real judgment (does this touch factory.py's registry at all)
# is a session/human call every time. Better to refuse an ambiguous one and
# ask than scaffold something that later gets misused as a Law 1 backdoor.
_BLOCKED_WORDS = ("signal", "strategy", "hypothesis", "buy", "sell",
                   "trade", "position", "backtest", "ledger")


def hire_count():
    """How many agents have actually been hired so far (not proposals)."""
    if not os.path.exists(HR_LOG_PATH):
        return 0
    text = open(HR_LOG_PATH).read()
    return text.count("\n- HIRED |")


def _validate(role_name, description):
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,30}", role_name):
        raise ValueError(f"role_name '{role_name}' must be lowercase_snake_case, "
                          "matching the existing agents/<name>/ convention.")
    if os.path.isdir(os.path.join(AGENTS_DIR, role_name)):
        raise ValueError(f"agents/{role_name}/ already exists -- this would be "
                          "an edit, not a hire. New agents get new names.")
    blob = (role_name + " " + description).lower()
    hit = next((w for w in _BLOCKED_WORDS if w in blob), None)
    if hit:
        raise ValueError(
            f"Refusing: '{hit}' suggests this role touches trading strategy "
            "territory, not team tooling. HR hires are scoped to helper "
            "roles only (per Het's 2026-08-26 clarification) -- a strategy "
            "idea goes through the normal mechanism-first hypothesis "
            "process in factory.py instead, never through here.")
    n = hire_count()
    if n >= PRE_AUTHORIZED_HIRES:
        raise ValueError(
            f"{n} agents already hired -- that's the pre-authorized cap "
            f"({PRE_AUTHORIZED_HIRES}). Hire #{n + 1} needs Het's explicit "
            "go-ahead first, not just a session's judgment.")


def propose_hire(role_name, reason):
    """Logs a proposal without creating anything -- for a session that
    wants to think out loud or flag a gap for Het before acting."""
    _validate(role_name, "PROPOSAL: " + reason)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    with open(HR_LOG_PATH, "a") as f:
        f.write(f"\n- PROPOSED | {ts} | {role_name} | {reason}\n")
    return f"Proposal logged for '{role_name}'. Not created yet."


def scaffold_agent(role_name, description, reason):
    """Actually creates agents/<role_name>/<role_name>.py + workspace.md,
    following the exact shape of the existing team (read-only/advisory
    stub, no ledger writes, no verdict influence), and logs the hire.
    Raises ValueError and creates nothing if _validate() rejects it."""
    _validate(role_name, description)

    role_dir = os.path.join(AGENTS_DIR, role_name)
    os.makedirs(role_dir)

    class_desc = description.strip()
    py_path = os.path.join(role_dir, f"{role_name}.py")
    with open(py_path, "w") as f:
        f.write(f'''"""
{role_name.replace("_", " ").title()} agent -- {class_desc}

Hired via agents/hr/hr.py, {datetime.date.today().isoformat()}. Same
guardrails as every other agent in this directory: read-only/advisory
only, no writes to factory_state/ledger.json, no influence on any
PROMOTE/DEMOTE verdict, no trading-signal logic of any kind. Extend the
functions below with real logic when there's a real, observed need for
it -- this file starts as a scaffold, not a finished agent.

See agents/{role_name}/workspace.md for this agent's own scratch notes
(never read by any trading logic).
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)


def report():
    """Stub -- fill in with this agent's actual detection/advisory logic."""
    print("--- {role_name.replace('_', ' ').title()} (advisory, read-only) ---")
    print("  Not yet implemented beyond scaffolding.")
    return []


if __name__ == "__main__":
    report()
''')

    ws_path = os.path.join(role_dir, "workspace.md")
    with open(ws_path, "w") as f:
        f.write(f"""# {role_name.replace("_", " ").title()}'s workspace

Personal scratch space for this agent -- notes, working data, anything
it wants to keep between runs. **Never read by any `sig_*` function or
factory.py's trading logic** (Law 1 safety: an agent's own notes can
never become a smuggled-in signal). Purely for the agent's own use and
for a human/session reading it to understand what this agent has been
doing.

(Empty at hire time -- the agent fills this in as it does real work.)
""")

    ts = datetime.date.today().isoformat()
    hire_number = hire_count() + 1
    with open(HR_LOG_PATH, "a") as f:
        f.write(f"\n- HIRED | {ts} | {role_name} | {reason} -- "
                f"agents/{role_name}/{role_name}.py + workspace.md scaffolded. "
                f"Hire #{hire_number}.\n")

    return f"Hired '{role_name}': {py_path}, {ws_path}. Remember to add it to agents/README.md's table by hand."


if __name__ == "__main__":
    print(f"Hires so far: {hire_count()} / {PRE_AUTHORIZED_HIRES} pre-authorized.")
