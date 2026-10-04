"""Portfolio aggregator (CE-2-03) -- READ-ONLY.

One top-level view across every asset-class profile: real-money exposure per
class against its ceiling, paper contestant counts, and a PAPER-VIEW portfolio
drawdown. Never writes a ledger, never changes a verdict, never touches RULES,
LADDER or COST_PER_SIDE (LADDER is only read).

    python3 -m portfolio.aggregate           # print the table
    python3 -m portfolio.aggregate --write   # also write factory_state/portfolio_view.json

Conventions (documented, not hidden):
  * real-money exposure = sum of LADDER[rung] over non-retired, non-permanent
    contestants with rung >= 1 (0 for everyone today).
  * paper contestants = non-retired, non-permanent, rung 0. The permanent
    benchmark is a yardstick, not a contestant, and is excluded from all counts.
  * ceilings (A 0.50 / B 0.30 / C 0.20) are MAXIMA of TOTAL real capital.
  * the portfolio drawdown is a PAPER VIEW: each class's best paper contestant
    equity curve, aligned on the dates common to all classes present, blended
    with equal weight (mean of equity levels). It is not a result and not a
    forecast; the real -10% / -15% rules (00_DESIGN.md s3.3) are evaluated on
    the real-money peak and are not evaluable while no real capital exists.
"""
import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEILINGS = {"A": 0.50, "B": 0.30, "C": 0.20}
DD_PAPER_RULE = -0.10
DD_KILL_RULE = -0.15
PAPER_LABEL = "PAPER VIEW -- not a result"


def _ladder():
    sys.path.insert(0, REPO_ROOT)
    import factory
    return list(factory.LADDER)


def _ledger_path(root, name):
    if name == "equity_nse":
        return os.path.join(root, "factory_state", "ledger.json")
    return os.path.join(root, "factory_state", name, "ledger.json")


def _load_profiles(root):
    pdir = os.path.join(root, "profiles")
    out = []
    for fname in sorted(os.listdir(pdir)):
        if not fname.endswith(".json"):
            continue
        name = fname[:-5]
        try:
            with open(os.path.join(pdir, fname)) as fh:
                prof = json.load(fh)
            if not isinstance(prof, dict):
                raise ValueError("profile must be a JSON object")
            out.append((name, prof, None))
        except (OSError, ValueError) as e:
            out.append((name, {}, f"unreadable profile: {e}"))
    return out


def equity_curve(contestant):
    """{date: equity} from a contestant's history rows [date, ret, equity];
    the last row for a repeated date wins."""
    curve = {}
    for row in contestant.get("history", []):
        curve[row[0]] = float(row[2])
    return curve


def max_drawdown(values):
    """Max peak-to-trough drawdown (<= 0) of a sequence of equity levels."""
    peak, worst = None, 0.0
    for v in values:
        peak = v if peak is None or v > peak else peak
        if peak:
            worst = min(worst, v / peak - 1.0)
    return worst


def blend_curves(curves):
    """Equal-weight blend (mean of levels) of curves over their common dates.
    Returns a sorted list of (date, equity); empty if none/no overlap."""
    curves = [c for c in curves if c]
    if not curves:
        return []
    dates = sorted(set.intersection(*(set(c) for c in curves)))
    return [(d, sum(c[d] for c in curves) / len(curves)) for d in dates]


def summarize_ledger(ledger, ladder):
    """Per-ledger numbers; raises on a malformed ledger (caller reports it)."""
    reg, con = ledger["registry"], ledger["contestants"]
    exposure = paper = retired = 0
    best = None  # (equity, name, curve)
    for name, s in con.items():
        if reg.get(name, {}).get("permanent"):
            continue
        if s["retired"]:
            retired += 1
            continue
        if s["rung"] >= 1:
            exposure += ladder[s["rung"]]
        else:
            paper += 1
            if best is None or s["equity"] > best[0]:
                best = (s["equity"], name, equity_curve(s))
    return dict(real_exposure=exposure, paper_count=paper, retired_count=retired,
                best_paper_equity=best[0] if best else None,
                best_paper_name=best[1] if best else None,
                _curve=best[2] if best else {})


def aggregate(root=REPO_ROOT, ladder=None):
    ladder = ladder if ladder is not None else _ladder()
    profiles, problems = [], []
    for name, prof, err in _load_profiles(root):
        row = dict(profile=name, **{"class": str(prof.get("class", "?"))},
                   enabled=prof.get("enabled") is True)
        row["class_letter"] = row["class"][:1].upper()
        path = _ledger_path(root, name)
        curve = {}
        if err:
            row["status"] = "ERROR"
            row["error"] = err
            problems.append(f"{name}: {err}")
        elif not os.path.isfile(path):
            row["status"] = "no ledger yet"
        else:
            try:
                with open(path) as fh:
                    summ = summarize_ledger(json.load(fh), ladder)
                curve = summ.pop("_curve")
                row.update(summ)
                row["status"] = "ok"
            except Exception as e:  # malformed ledger: report, never raise
                row["status"] = "ERROR"
                row["error"] = f"malformed ledger {path}: {type(e).__name__}: {e}"
                problems.append(f"{name}: {row['error']}")
        row["_curve"] = curve
        profiles.append(row)

    ok = [p for p in profiles if p["status"] == "ok"]
    total_real = sum(p["real_exposure"] for p in ok)
    classes = {}
    for letter, ceil in CEILINGS.items():
        members = [p for p in ok if p["class_letter"] == letter]
        exp = sum(p["real_exposure"] for p in members)
        entry = dict(ceiling=ceil, real_exposure=exp, profiles=[p["profile"] for p in members])
        if total_real > 0:
            share = exp / total_real
            entry["share_of_real"] = share
            entry["ceiling_text"] = (f"{share:.1%} of real capital vs ceiling {ceil:.0%}"
                                     + ("  [OVER CEILING]" if share > ceil else ""))
        else:
            entry["share_of_real"] = None
            entry["ceiling_text"] = f"no real capital (ceiling {ceil:.0%} max)"
        # class paper curve = best paper contestant across the class's profiles
        cands = [p for p in members if p.get("best_paper_equity") is not None]
        if cands:
            top = max(cands, key=lambda p: p["best_paper_equity"])
            entry["best_paper_profile"] = top["profile"]
            entry["best_paper_name"] = top["best_paper_name"]
            entry["best_paper_equity"] = top["best_paper_equity"]
            entry["_curve"] = top["_curve"]
        else:
            entry["_curve"] = {}
        classes[letter] = entry

    blended = blend_curves([c["_curve"] for c in classes.values()])
    paper_view = dict(label=PAPER_LABEL,
                      classes_blended=[k for k, c in classes.items() if c["_curve"]],
                      points=len(blended),
                      first_date=blended[0][0] if blended else None,
                      last_date=blended[-1][0] if blended else None,
                      max_drawdown=max_drawdown(v for _, v in blended) if blended else None)
    real_rule = ("not evaluable: no real capital" if total_real == 0 else
                 "real-money drawdown not tracked yet -- evaluate manually")
    for p in profiles:
        p.pop("_curve", None)
    for c in classes.values():
        c.pop("_curve", None)
    return dict(profiles=profiles, classes=classes, total_real_exposure=total_real,
                paper_view=paper_view, problems=problems,
                drawdown_rules=dict(paper_trigger=DD_PAPER_RULE, kill_trigger=DD_KILL_RULE,
                                    status=real_rule, kill_tripped=False))


def format_table(view):
    L = ["=== Portfolio aggregator (read-only) ===",
         f"Total real-money exposure: Rs {view['total_real_exposure']:,}",
         "", "Per profile:",
         f"  {'profile':<14}{'class':<6}{'real Rs':>9}{'paper':>7}{'retired':>9}{'best paper eq':>15}  status"]
    for p in view["profiles"]:
        if p["status"] != "ok":
            L.append(f"  {p['profile']:<14}{p['class']:<6}{'-':>9}{'-':>7}{'-':>9}{'-':>15}  {p['status']}"
                     + (f" ({p['error']})" if p.get("error") else ""))
            continue
        be = f"{p['best_paper_equity']:.4f}" if p["best_paper_equity"] is not None else "-"
        L.append(f"  {p['profile']:<14}{p['class']:<6}{p['real_exposure']:>9,}"
                 f"{p['paper_count']:>7}{p['retired_count']:>9}{be:>15}  ok")
    L += ["", "Per class (ceilings are MAXIMA of total real capital):"]
    for letter, c in view["classes"].items():
        L.append(f"  Class {letter}: Rs {c['real_exposure']:,} -- {c['ceiling_text']}")
    pv = view["paper_view"]
    L += ["", f"Portfolio drawdown [{pv['label']}]:"]
    if pv["max_drawdown"] is None:
        L.append("  no overlapping paper history to blend")
    else:
        L.append(f"  equal-weight blend of best paper contestant per class "
                 f"({','.join(pv['classes_blended'])}), {pv['points']} common dates "
                 f"{pv['first_date']}..{pv['last_date']}: max drawdown {pv['max_drawdown']:.2%}")
    dr = view["drawdown_rules"]
    L.append(f"Real-money drawdown rules ({dr['paper_trigger']:.0%} -> B,C to paper; "
             f"{dr['kill_trigger']:.0%} -> KILL): {dr['status']}; kill tripped: no")
    if view["problems"]:
        L += ["", "PROBLEMS (reported, not raised):"] + [f"  - {x}" for x in view["problems"]]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only portfolio aggregator")
    ap.add_argument("--write", action="store_true",
                    help="also write factory_state/portfolio_view.json")
    args = ap.parse_args(argv)
    view = aggregate()
    print(format_table(view))
    if args.write:
        out = os.path.join(REPO_ROOT, "factory_state", "portfolio_view.json")
        with open(out, "w") as fh:
            json.dump(view, fh, indent=1, sort_keys=True)
        print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
