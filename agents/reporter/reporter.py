"""
Reporter agent -- plain-English translation of factory.report()'s output.

NEW logic, but purely presentational: no new financial computation, no
ledger writes, no effect on any verdict. Exists because Het has said
explicitly (see .autonomous/operator_profile.md) that he's self-taught and
wants things explained in plain language, not just shown as a raw table.
This module takes report()'s already-computed rows/evolved/born lists and
renders a short human summary -- it does not decide anything.

USAGE (called additively from factory.report(), after the ledger is saved):
    from agents.reporter.reporter import weekly_digest
"""
import factory as f


def weekly_digest(rows, evolved, born, ledger_state=None):
    """rows: list of dicts, same shape as factory.report()'s `rows` list.
    evolved: list of contestant names replaced by the advisor layer this
      round (propose_evolutions()'s return value).
    born: list of new contestant names from this round's breeding
      (attempt_breeding()'s return value).
    Prints, and also returns, a short plain-language summary -- callers
    that just want the text (e.g. a future notification channel) can use
    the return value instead of parsing stdout."""
    state = ledger_state or f.load_state()
    con = state["contestants"]

    live = [r for r in rows]
    promotions = [r for r in live if r["verdict"] == "PROMOTE"]
    demotions = [r for r in live if r["verdict"] == "DEMOTE"]
    retired_now = [n for n in (evolved or [])
                   if con.get(n, {}).get("retired")]

    best = max(live, key=lambda r: r["equity"], default=None)
    worst = min(live, key=lambda r: r["equity"], default=None)

    lines = ["\n--- Weekly digest (plain-English) ---"]
    lines.append(f"  {len(live)} strategies are currently active.")

    if promotions:
        names = ", ".join(r["strategy"] for r in promotions)
        lines.append(f"  {len(promotions)} strategy(ies) did well enough to "
                      f"move up a level (more real money on the line if you "
                      f"choose to fund it): {names}.")
    else:
        lines.append("  No strategy earned a promotion this round -- that's "
                      "normal and expected in Phase 0/1, not a failure.")

    if demotions:
        names = ", ".join(r["strategy"] for r in demotions)
        lines.append(f"  {len(demotions)} strategy(ies) lost too much and "
                      f"got moved down a level (or retried from scratch if "
                      f"already on paper): {names}.")

    if evolved:
        lines.append(f"  {len(evolved)} underperforming paper strategy(ies) "
                      f"were swapped out for a new attempt based on what "
                      f"historical research suggests works better: "
                      f"{', '.join(evolved)}.")

    if born:
        lines.append(f"  {len(born)} new strategy(ies) were 'bred' from two "
                      f"profitable parents (a mix of their approaches, "
                      f"starting fresh on paper -- no real money involved): "
                      f"{', '.join(born)}.")

    if best is not None:
        lines.append(f"  Best performer right now: {best['strategy']} "
                      f"(equity {best['equity']}, meaning "
                      f"{'a gain' if best['equity'] >= 1 else 'a loss'} of "
                      f"{abs(best['equity'] - 1) * 100:.1f}% since it started).")
    if worst is not None and worst is not best:
        lines.append(f"  Weakest performer: {worst['strategy']} "
                      f"(equity {worst['equity']}).")

    lines.append("  Reminder: every strategy above rung 0 is still paper "
                  "money unless you personally funded and placed a real "
                  "trade -- nothing here spends real capital on its own.")

    text = "\n".join(lines)
    print(text)
    return text
