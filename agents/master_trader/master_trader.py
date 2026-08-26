"""
Master Trader agent -- synthesizes the rest of the team into one clear
recommendation. Read-only, advisory. Decides NOTHING that isn't already
decided elsewhere.

Origin: Het, 2026-08-26, asked for an agent that "organises everything,
decides who gets real cash later on, develops his own risk management
strategy, decides maximum output, reviews agent code with the IT guy to
make necessary decisions." Asked him directly what "decides" meant --
he confirmed he wanted it able to adjust the promotion RULES, set risk
parameters/position sizing, and approve its own merges. DECLINED that,
explicitly, even offered under time pressure ("ask for all the
permission you want, I'm getting on a flight") -- see
.autonomous/het_directives.md for the full reasoning. That version is
not built and should not be built without a separate, unhurried
conversation with Het specifically about it.

This is the version that WAS built: same authority tier as
Judge/Risk Manager/Reporter above it. It:
  - never writes factory_state/ledger.json
  - never changes RULES, LADDER, or COST_PER_SIDE
  - never decides who is eligible for promotion (that's judge.py
    re-deriving factory.report()'s own mechanical math -- this module
    just reads judge's answer)
  - never sets or suggests specific risk-parameter VALUES (that's
    still a human call) -- it can only flag what risk_manager.py
    already flags, synthesized into one place
  - never merges a PR or approves a merge -- see it_guy_protocol.md;
    this agent can add a second opinion to a proposed fix, nothing more

USAGE (read-only, safe to call any time):
    from agents.master_trader.master_trader import recommend
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

import factory as f
from agents.judge.judge import who_is_eligible_for_promotion
from agents.risk_manager.risk_manager import (
    aggregate_real_money_exposure, sector_concentration,
    portfolio_drawdown_correlation_flag,
)
from agents.researcher.researcher import graveyard


def recommend(ledger_state=None):
    """One synthesized recommendation, pulling together what Judge,
    Risk Manager, and Researcher already independently compute. Returns
    a dict for a caller (a session, or a future UI) to act on -- but
    "act on" always means "show Het," never "execute automatically."
    Nothing here is a new computation; everything is a re-read of an
    existing agent's own read-only output."""
    state = ledger_state or f.load_state()

    eligible = who_is_eligible_for_promotion(state)
    exposure = aggregate_real_money_exposure(state)
    conc = sector_concentration(state)
    flagged, below, live_n = portfolio_drawdown_correlation_flag(state)
    grave = graveyard(state)

    notes = []
    if eligible:
        notes.append(
            f"{len(eligible)} contestant(s) mechanically clear every PROMOTE "
            f"threshold right now: {', '.join(eligible)}. This is judge.py's "
            f"re-derivation of report()'s own math, not a new decision -- "
            f"promoting them for real money is still Het's own action.")
    else:
        notes.append("Nobody currently clears every PROMOTE threshold -- "
                      "normal, not a problem.")

    if exposure:
        notes.append(f"[!] Real-money exposure is Rs {exposure:,}, not Rs 0 -- "
                      "verify this matches a fresh, explicit authorization on "
                      "record, not silent drift.")
    else:
        notes.append("Real-money exposure: Rs 0 (expected).")

    if flagged:
        notes.append(f"[!] {below}/{live_n} live contestants are simultaneously "
                      "in elevated drawdown -- possible correlated regime move, "
                      "worth a human look.")

    if conc:
        top_sector = max(conc.items(), key=lambda kv: kv[1]["contestants"])
        if top_sector[1]["contestants"] >= live_n * 0.5 and live_n > 0:
            notes.append(f"[!] Sector concentration: {top_sector[0]} holds "
                          f"{top_sector[1]['contestants']}/{live_n} live "
                          f"contestants -- worth knowing before adding more "
                          f"of the same sector.")

    if grave:
        notes.append(f"{len(grave)} setup(s) already tried and retired -- "
                      "propose_evolutions() already avoids exact repeats of "
                      "these automatically (factory.already_failed()).")

    return dict(
        eligible_for_promotion=eligible,
        real_money_exposure=exposure,
        sector_concentration=conc,
        correlated_drawdown_flag=flagged,
        graveyard_size=len(grave),
        notes=notes,
    )


def second_opinion_on_fix(description, files_touched):
    """For the IT-guy protocol: a lightweight, code-only sanity check on
    a PROPOSED fix's description before it's surfaced to Het -- catches
    the most obvious guardrail violations by keyword, same defense-in-
    depth pattern as agents/hr/hr.py's blocked-word check. This is NOT
    code review (no LLM judgment runs here) and NEVER approves or blocks
    a merge -- it only adds a flag line to what the IT-guy protocol
    already tells Het. The actual judgment call stays with whichever
    session is doing the fix, same as every other agent in this
    directory: detect, never decide.

    files_touched: list of repo-relative paths the fix changed.
    """
    warnings = []
    guarded_files = ("factory_state/ledger.json",)
    guarded_symbols_in_factory = ("RULES", "LADDER", "COST_PER_SIDE")

    for path in files_touched:
        if path in guarded_files:
            warnings.append(f"Touches {path} directly -- this file is only "
                             "ever written by factory.py's save_state(), "
                             "never hand-edited.")
        if path == "factory.py":
            for sym in guarded_symbols_in_factory:
                if sym in description:
                    warnings.append(
                        f"Description mentions '{sym}' while touching "
                        f"factory.py -- if this fix changes that constant's "
                        f"VALUE (not just reads it), it needs Het's fresh, "
                        f"explicit, separate authorization before merge, "
                        f"same as any other RULES/LADDER/COST_PER_SIDE change.")

    return warnings


if __name__ == "__main__":
    result = recommend()
    print("\n--- Master Trader (advisory, read-only, synthesizes the team) ---")
    for note in result["notes"]:
        print(f"  {note}")
