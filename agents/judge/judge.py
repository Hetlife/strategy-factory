"""
Judge agent -- read-only wrapper around factory.py's promotion/demotion logic.

Does NOT duplicate the verdict computation. factory.report() remains the
single source of truth for PROMOTE/DEMOTE/hold decisions and is the only
function that writes ledger.json. This module only re-derives the same
per-contestant numbers report() already computes, for a human-readable
explanation of *why* a given contestant got the verdict it did -- useful
when Het asks "why didn't X get promoted" without having to read report()'s
raw table.

USAGE (read-only, safe to call any time):
    from agents.judge.judge import explain_verdict, who_is_eligible_for_promotion
"""
import numpy as np

import factory as f


def _row_for(name, s, R=None):
    R = R or f.RULES
    n = max(s["days_in_market"], 1)
    mean = s["sum_ret"] / n
    if s["days_in_market"] < f.MIN_SHARPE_SAMPLE_DAYS:
        sharpe = float("nan")
    else:
        var = max(s["sum_sq"] / n - mean ** 2, 1e-12)
        sharpe = mean / np.sqrt(var) * np.sqrt(252)
    dd = s["equity"] / s["peak"] - 1
    return dict(mean=mean, sharpe=sharpe, dd=dd)


def explain_verdict(name, ledger_state=None):
    """Plain-language reasons a contestant did/didn't get PROMOTE, using the
    exact same RULES thresholds factory.report() checks. Read-only: does not
    call report() and does not touch ledger.json."""
    state = ledger_state or f.load_state()
    con = state["contestants"]
    if name not in con:
        return f"{name}: not found in ledger."
    s = con[name]
    if s["retired"]:
        return f"{name}: retired, no longer eligible for any verdict."
    R = f.RULES
    row = _row_for(name, s, R)
    reasons = []
    checks = [
        ("days_on_rung", s["days_on_rung"], R["min_days_on_rung"], ">="),
        ("trades", s["trades"], R["min_trades"], ">="),
        ("expectancy (mean daily net return)", round(row["mean"], 6),
         R["min_expectancy"], ">="),
        ("sharpe", round(row["sharpe"], 3) if not np.isnan(row["sharpe"])
         else "NaN (under min sample)", R["min_sharpe"], ">="),
    ]
    for label, have, need, op in checks:
        ok = (isinstance(have, (int, float)) and not
              (isinstance(have, float) and np.isnan(have)) and have >= need)
        reasons.append(f"  {label}: have {have}, need {op} {need} -> "
                        f"{'OK' if ok else 'NOT MET'}")
    if row["dd"] < R["max_drawdown"]:
        verdict = "DEMOTE (drawdown breach)"
    elif all("OK" in r for r in reasons):
        verdict = "PROMOTE"
    else:
        verdict = "hold"
    return (f"{name} (rung {s['rung']}): verdict = {verdict}\n"
            f"  drawdown: {row['dd']*100:.1f}%, limit {R['max_drawdown']*100:.1f}%\n"
            + "\n".join(reasons))


def who_is_eligible_for_promotion(ledger_state=None):
    """List of contestant names currently meeting every PROMOTE threshold.
    Cheap sanity check against report()'s own printed verdicts -- if this
    list disagrees with report()'s output, that's a bug in one of the two,
    not a second opinion to act on directly."""
    state = ledger_state or f.load_state()
    con = state["contestants"]
    R = f.RULES
    eligible = []
    for name, s in con.items():
        if s["retired"]:
            continue
        row = _row_for(name, s, R)
        if (row["dd"] >= R["max_drawdown"]
                and s["days_on_rung"] >= R["min_days_on_rung"]
                and s["trades"] >= R["min_trades"]
                and row["mean"] >= R["min_expectancy"]
                and row["sharpe"] >= R["min_sharpe"]):
            eligible.append(name)
    return eligible
