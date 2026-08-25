"""
Researcher agent -- thin wrapper around advisors.py's training layer.

Does NOT duplicate the backtest/scoring logic. advisors.py remains the only
place that fetches historical prices, backtests the parameter grid, and
writes parameter_bank.json. This module just exposes convenient read
accessors so other agents (or a human) can ask "what does the researcher
currently believe is the best parameter set for X" without re-reading raw
JSON structure.

USAGE:
    from agents.researcher.researcher import train, top_candidate
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
