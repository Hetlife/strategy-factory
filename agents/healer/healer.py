"""
Healer agent -- runs between operations, looks for things that need fixing,
reports them plainly, and NEVER fixes anything itself.

Origin: Het asked for "an agent that goes through everything in between
operations and sees what needs fixing, asks you for permission, and lets
the work happen in background as you find fit" -- named it after DNA/RNA
repair mechanisms that continuously scan for and flag damage rather than
silently patching it. This is the code-side half of that: the deterministic
detection layer. The other half -- deciding what a finding means and
whether/how to fix it -- stays a judgment call for whichever session (or
Het) reads the report, exactly like every other agent in this directory.

Read-only, advisory only, same guardrails as risk_manager/reporter: no
ledger writes, no code edits, no verdict influence. It exists specifically
so that repo-consistency checking stops being something a session
re-derives by hand (many tool calls, many tokens) every time, and becomes
something code does once, deterministically, for free -- see
tools/health_check.py, which does the actual detection work. This module
is the thin presentation/orchestration layer over it.

USAGE (read-only, safe to call any time, including from a Routine prompt):
    from agents.healer.healer import report
    findings = report()
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import health_check


def report(ledger_path=None, state_path=None):
    """Runs every deterministic check and prints a plain-language summary.
    Returns the raw findings list too, for a caller that wants to act on
    it programmatically rather than just read the printout."""
    findings = health_check.run_all(ledger_path, state_path)
    print("\n--- Healer (advisory, read-only, code-only detection) ---")
    if not findings:
        print("  Nothing found. Repo trackers and ledger are internally "
              "consistent as of this check.")
        return findings

    errors = [f for f in findings if f[0] == "error"]
    warnings = [f for f in findings if f[0] == "warning"]
    infos = [f for f in findings if f[0] == "info"]

    if errors:
        print(f"  {len(errors)} thing(s) that look like real problems:")
        for _, msg in errors:
            print(f"    [!] {msg}")
    if warnings:
        print(f"  {len(warnings)} thing(s) worth a look:")
        for _, msg in warnings:
            print(f"    [~] {msg}")
    if infos:
        print(f"  {len(infos)} minor note(s), probably fine:")
        for _, msg in infos:
            print(f"    [.] {msg}")

    print("  None of these were auto-fixed -- the healer only detects. "
          "A session (or Het) decides what, if anything, to do about each one.")
    return findings


if __name__ == "__main__":
    report()
