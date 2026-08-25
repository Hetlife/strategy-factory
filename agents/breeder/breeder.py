"""
Breeder agent -- thin, read-only wrapper around factory.py's three breeding
mechanisms (spawn_neighbor on promotion, advisor_evolve on paper-tier
straggler replacement, crossover on profitable top-N mate selection).

Does NOT duplicate any breeding logic and does NOT create contestants --
factory.report() is the only place that calls spawn_children(),
propose_evolutions(), and attempt_breeding(), and the only place that writes
ledger.json. This module just reads the `lineage` field factory.py already
records on every contestant and renders it as a family tree, since the raw
JSON is hard to read by eye.

USAGE (read-only, safe to call any time):
    from agents.breeder.breeder import lineage_tree
"""
import factory as f

_MECHANISM_LABEL = {
    "spawn_neighbor": "promoted->bred neighbor",
    "advisor_evolve": "advisor-evolved replacement",
    "crossover": "two-parent mate breeding",
}


def lineage_tree(ledger_state=None):
    """Returns {child_name: description} for every contestant with a
    recorded lineage (None = an original seed_registry() entry, not bred)."""
    state = ledger_state or f.load_state()
    con = state["contestants"]
    tree = {}
    for name, s in con.items():
        lineage = s.get("lineage")
        if not lineage:
            continue
        mech = _MECHANISM_LABEL.get(lineage.get("mechanism"),
                                     lineage.get("mechanism", "unknown"))
        parents = ", ".join(lineage.get("parents", [])) or "unknown"
        tree[name] = (f"gen {lineage.get('gen', '?')}, via {mech}, "
                       f"parent(s): {parents}")
    return tree
