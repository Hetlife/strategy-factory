"""
Researcher agent -- thin wrapper around advisors.py's training layer.

Does NOT duplicate the backtest/scoring logic. advisors.py remains the only
place that fetches historical prices, backtests the parameter grid, and
writes parameter_bank.json. This module just exposes convenient read
accessors so other agents (or a human) can ask "what does the researcher
currently believe is the best parameter set for X" without re-reading raw
JSON structure.

USAGE:
    from agents.researcher.researcher import train, top_candidate, graveyard, already_failed
"""
import advisors as a
import factory as f


def train():
    """Runs the real (network-dependent, Yahoo Finance) training pass.
    Delegates entirely to advisors.train() -- no logic here."""
    return a.train()


def top_candidate(family, sector, bank=None):
    """Best-ranked parameter set for a (family, sector) bucket, per the
    existing parameter_bank.json ensemble ranking. Returns None if the
    bucket doesn't exist yet (e.g. training hasn't run in this environment
    -- Yahoo Finance is unreachable from Claude Code sandboxes, see
    CLAUDE.md known environment quirks)."""
    bank = bank or f.load_parameter_bank().get("bank", {})
    bucket = bank.get(family, {}).get(sector)
    if not bucket:
        return None
    return bucket[0]   # already rank-sorted by advisors.py's ensemble_rank


def graveyard(ledger_state=None):
    """What's already been tried and failed -- see factory.graveyard()'s
    docstring for the full rationale (this is a thin re-export, the real
    logic lives in factory.py since propose_evolutions() also needs it and
    factory.py can't import agents.researcher without a circular import)."""
    return f.graveyard(ledger_state)


def already_failed(candidate_params, ledger_state=None):
    """True only for an EXACT repeat of an already-retired setup -- see
    factory.already_failed()'s docstring. Deliberately narrow: never used
    to invent a new hypothesis (Law 1), only to avoid proposing an exact
    repeat of a setup that's already proven not to work."""
    return f.already_failed(candidate_params, ledger_state)
