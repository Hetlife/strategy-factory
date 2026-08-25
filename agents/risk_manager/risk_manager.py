"""
Risk manager agent -- NEW logic, but strictly read-only and advisory.

Never writes ledger.json, never changes a verdict, never touches RULES,
LADDER, or COST_PER_SIDE. Everything here is a second set of eyes on the
SAME state factory.report() already computed, looking for portfolio-level
risk that a per-contestant verdict can't see by itself (concentration
across contestants, real-money exposure, correlated drawdowns). If this
module's output ever disagrees with the intent of "no real money is at
risk in Phase 0/1," that is a signal to stop and tell Het, not something
to fix by editing this file to make the number look better -- see
EXECUTION_PLAN.md Section 5(f) kill-condition language.

USAGE (read-only, safe to call any time, including from factory.report()):
    from agents.risk_manager.risk_manager import report
"""
import factory as f


def sector_concentration(ledger_state=None):
    """Live (non-retired) contestant count and rung-weighted capital by
    sector, keyed off factory.UNIVERSE. A crude concentration check --
    real portfolio correlation isn't computed here, just headcount/capital
    by sector as an early warning, not a risk model."""
    state = ledger_state or f.load_state()
    reg, con = state["registry"], state["contestants"]
    sector_of = {t: sec for sec, tickers in f.UNIVERSE.items() for t in tickers}

    def contestant_sector(name):
        params = reg.get(name, {})
        sec = params.get("sector")
        if sec:
            return sec
        leader = params.get("leader") or params.get("proxy")
        return sector_of.get(leader, "unknown")

    out = {}
    for name, s in con.items():
        if s["retired"]:
            continue
        sec = contestant_sector(name)
        bucket = out.setdefault(sec, {"contestants": 0, "capital": 0})
        bucket["contestants"] += 1
        bucket["capital"] += f.LADDER[s["rung"]]
    return out


def aggregate_real_money_exposure(ledger_state=None):
    """Sum of LADDER capital across every contestant at rung >= 1. Should
    be Rs 0 for the entire duration of Phase 0/1 -- this project has never
    deployed real capital. A nonzero value here without a matching, freshly
    authorized decision in AUTONOMOUS_TODO.md is exactly the kind of thing
    this agent exists to catch."""
    state = ledger_state or f.load_state()
    con = state["contestants"]
    total = sum(f.LADDER[s["rung"]] for s in con.values()
                if not s["retired"] and s["rung"] >= 1)
    return total


def portfolio_drawdown_correlation_flag(ledger_state=None, threshold=-0.08):
    """Flags when more than half of live contestants are simultaneously
    below `threshold` drawdown from their own peak -- a crude proxy for
    "the whole arena is losing together," which a per-contestant DEMOTE
    check can't see (each one might individually still be above
    RULES['max_drawdown']). Advisory only -- does not affect any verdict."""
    state = ledger_state or f.load_state()
    con = state["contestants"]
    live = [s for s in con.values() if not s["retired"]]
    if not live:
        return False, 0, 0
    below = sum(1 for s in live if (s["equity"] / s["peak"] - 1) < threshold)
    return (below > len(live) / 2), below, len(live)


def report(ledger_state=None):
    """Prints a short advisory summary. Called additively from
    factory.report(), after the ledger has already been saved -- never
    called before, and never in a way that could influence a verdict."""
    state = ledger_state or f.load_state()
    print("\n--- Risk Manager (advisory, read-only) ---")

    exposure = aggregate_real_money_exposure(state)
    print(f"  Real-money exposure across all rungs: Rs {exposure:,}"
          + ("" if exposure == 0 else "  [!] NONZERO -- verify this was "
             "a fresh, explicit, in-session authorization, not silent drift."))

    conc = sector_concentration(state)
    if conc:
        pieces = []
        for sec, v in sorted(conc.items()):
            capital_note = f", Rs {v['capital']:,}" if v["capital"] else ""
            pieces.append(f"{sec}: {v['contestants']} live{capital_note}")
        print(f"  Sector concentration (live contestants): {', '.join(pieces)}")

    flagged, below, live_n = portfolio_drawdown_correlation_flag(state)
    if flagged:
        print(f"  [!] {below}/{live_n} live contestants are simultaneously "
              f"in an elevated drawdown -- possible correlated regime move, "
              f"worth a human look even though no single verdict is DEMOTE.")
    else:
        print(f"  Drawdown correlation check: {below}/{live_n} live "
              f"contestants in elevated drawdown -- not flagged.")
    return dict(real_money_exposure=exposure, sector_concentration=conc,
                correlated_drawdown_flag=flagged)
