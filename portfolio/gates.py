"""Capital activation gates (CE-4-01) -- READ-ONLY evaluator, prints only.

For each asset class (A shield, B crypto, C derivatives) evaluates the five
gates of docs/capital_engine/00_DESIGN.md s6 and prints GREEN / AMBER / RED
with a reason per gate. It never writes a file, never changes a verdict, never
touches RULES, LADDER, COST_PER_SIDE or any ledger, and never acts: a GREEN
class still needs a human. RED anywhere = no real money.

    python3 tools/gates_report.py       # or: python3 -m portfolio.gates

Gates (any RED -> class RED; every gate GREEN except G4 -> AMBER; all -> GREEN):
  G1 evidence       >= 1 non-permanent, non-retired contestant at rung >= 1 with
                    days_on_rung >= RULES['min_days_on_rung'] in the class's ledgers
  G2 independent    a file docs/capital_engine/validation/<class>_*.md exists and
     validation     names an ISO date (existence + date only; a human reads it)
  G3 portfolio      aggregator kill rule not tripped AND the class's share of
     limits         total real capital after activating (AUTHORIZE amount, else
                    LADDER[1]) stays <= ceiling (B 30 / C 20 %, the aggregator's
                    CEILINGS; A is a 50% FLOOR so its cap here is 100%)
  G4 owner          a dated line in .autonomous/het_directives.md, outside the
     authorization  NEEDS HET section, starting '- 20', containing
                    'AUTHORIZE REAL CAPITAL <class> <contestant> <amount>' after
                    stripping ~~strikethrough~~ and `backtick` spans; lines that
                    say 'example' / 'e.g.' are ignored. Absent -> AMBER (a human
                    must still write it); never RED.
  G5 infrastructure def kill_switch_active in factory.py AND
                    docs/capital_engine/EXECUTION_ADAPTER_CONTRACT.md exist

Class C is ALWAYS RED (design s8 A4: no derivatives logic exists or is authorized).
"""
import datetime
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from portfolio import aggregate as agg  # noqa: E402

GREEN, AMBER, RED = "GREEN", "AMBER", "RED"
CLASSES = ("A", "B", "C")
GATE_NAMES = {"G1": "evidence", "G2": "independent validation", "G3": "portfolio limits",
              "G4": "owner authorization", "G5": "infrastructure"}
# Class A's 50% is a FLOOR ("50% floor, up to 100%", design s2) and day one is
# 100% A1 (design s3.1), so only B and C are capped by the aggregator's ceilings;
# A's cap here is 1.0. (The aggregator still prints A against 0.50 -- flagged in
# the CE-4-01 evidence packet, not changed here: read-only scope.)
GATE_CEILINGS = dict(agg.CEILINGS)   # A is 1.0 (floor 50%, cap 100%) since 2026-10-04
C_REASON = "gated: no derivatives logic exists and none is authorized (design section 8 A4)"

_AUTH_RE = re.compile(r"AUTHORIZE REAL CAPITAL\s+([ABC])\s+(\S+)\s+(\d[\d,_]*)")
_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


def _rules_min_days():
    import factory
    return factory.RULES["min_days_on_rung"]


def _class_ledgers(root, letter):
    """[(profile, ledger_dict)] for profiles of this class; plus problem strings."""
    found, problems = [], []
    import json
    for name, prof, err in agg._load_profiles(root):
        if err or str(prof.get("class", "?"))[:1].upper() != letter:
            continue
        path = agg._ledger_path(root, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as fh:
                found.append((name, json.load(fh)))
        except (OSError, ValueError) as e:
            problems.append(f"{name}: unreadable ledger ({type(e).__name__})")
    return found, problems


def gate_g1(root, letter, min_days=None):
    min_days = _rules_min_days() if min_days is None else min_days
    ledgers, problems = _class_ledgers(root, letter)
    if not ledgers:
        return RED, "G1 unmet: no ledger exists for this class (no paper evidence at all)" + (
            f"; {'; '.join(problems)}" if problems else "")
    total = promoted = 0
    best = None
    for prof, led in ledgers:
        try:
            reg, con = led["registry"], led["contestants"]
            for name, s in con.items():
                if reg.get(name, {}).get("permanent") or s["retired"]:
                    continue
                total += 1
                if s["rung"] >= 1:
                    promoted += 1
                    if s["days_on_rung"] >= min_days:
                        return GREEN, (f"{prof}/{name} at rung {s['rung']} for "
                                       f"{s['days_on_rung']}d (>= {min_days})")
                    if best is None or s["days_on_rung"] > best[0]:
                        best = (s["days_on_rung"], f"{prof}/{name}")
        except (KeyError, TypeError, AttributeError) as e:
            problems.append(f"{prof}: malformed ledger ({type(e).__name__}: {e})")
    if problems:
        return RED, "G1 unmet: could not read ledger(s): " + "; ".join(problems)
    if best:
        return RED, (f"G1 unmet: {promoted} contestant(s) at rung >= 1 but best has "
                     f"{best[0]}d on rung ({best[1]}), need {min_days}")
    return RED, (f"G1 unmet: zero promotions ever -- 0 of {total} live paper contestants "
                 f"at rung >= 1 (ladder, Law 3)")


def gate_g2(root, letter):
    vdir = os.path.join(root, "docs", "capital_engine", "validation")
    files = []
    if os.path.isdir(vdir):
        files = sorted(f for f in os.listdir(vdir)
                       if f.startswith(letter + "_") and f.endswith(".md"))
    if not files:
        return RED, (f"G2 unmet: no docs/capital_engine/validation/{letter}_*.md "
                     "(independent validation, different session, LucyOS C9)")
    dated = []
    for f in files:
        try:
            with open(os.path.join(vdir, f), errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        if _DATE_RE.search(f) or _DATE_RE.search(text):
            dated.append(f)
    if not dated:
        return RED, f"G2 unmet: {', '.join(files)} exist but none names a date"
    return GREEN, f"validation file present and dated: {dated[0]} (content not judged here)"


def _directive_lines(root):
    """Dated '- 20...' lines outside the '## NEEDS HET' section."""
    path = os.path.join(root, ".autonomous", "het_directives.md")
    try:
        with open(path, errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    out, in_needs = [], False
    for line in lines:
        if line.startswith("#"):
            in_needs = "NEEDS HET" in line
            continue
        if not in_needs and line.startswith("- 20"):
            out.append(line)
    return out


def find_authorization(root, letter, today=None):
    """(date, contestant, amount_int) of the last qualifying G4 line, or None."""
    today = today or datetime.date.today()
    lines = _directive_lines(root)
    hit = None
    for line in lines or []:
        d = line[2:12]
        try:
            if datetime.date.fromisoformat(d) > today:
                continue
        except ValueError:
            continue
        clean = re.sub(r"~~.*?~~", " ", line)
        clean = re.sub(r"`[^`]*`", " ", clean)
        if re.search(r"example|e\.g\.", clean, re.I):
            continue
        for m in _AUTH_RE.finditer(clean):
            if m.group(1) == letter:
                hit = (d, m.group(2), int(re.sub(r"[,_]", "", m.group(3))))
    return hit


def gate_g3(root, letter, ladder=None, auth=None):
    try:
        ladder = ladder if ladder is not None else agg._ladder()
        view = agg.aggregate(root, ladder)
    except Exception as e:  # never raise from a read-only evaluator
        return RED, f"G3 unmet: aggregator failed ({type(e).__name__}: {e})"
    if view["problems"]:
        return RED, "G3 unmet: aggregator reports problems: " + "; ".join(view["problems"])
    dr = view["drawdown_rules"]
    if dr["kill_tripped"]:
        return RED, f"G3 unmet: portfolio drawdown kill rule tripped ({dr['kill_trigger']:.0%})"
    amount = auth[2] if auth else ladder[1]
    basis = "authorized amount" if auth else "rung-1 amount"
    ceil = GATE_CEILINGS[letter]
    cls_exp = view["classes"][letter]["real_exposure"]
    share = (cls_exp + amount) / (view["total_real_exposure"] + amount)
    if share > ceil:
        return RED, (f"G3 unmet: class {letter} would hold {share:.0%} of real capital after "
                     f"activating Rs {amount:,} ({basis}), ceiling {ceil:.0%}")
    return GREEN, (f"kill rule not tripped; class {letter} {share:.0%} of real capital after "
                   f"Rs {amount:,} ({basis}) <= ceiling {ceil:.0%}")


def gate_g4(root, letter, today=None):
    if _directive_lines(root) is None:
        return AMBER, "G4 awaiting owner: .autonomous/het_directives.md unreadable"
    hit = find_authorization(root, letter, today)
    if hit:
        return GREEN, f"dated line {hit[0]}: AUTHORIZE REAL CAPITAL {letter} {hit[1]} {hit[2]:,}"
    return AMBER, (f"G4 awaiting owner: no dated 'AUTHORIZE REAL CAPITAL {letter} <contestant> "
                   "<amount>' line in het_directives.md (a human must write it, in session)")


def gate_g5(root):
    missing = []
    try:
        with open(os.path.join(root, "factory.py"), errors="replace") as fh:
            if not re.search(r"^def kill_switch_active\(", fh.read(), re.M):
                missing.append("factory.kill_switch_active")
    except OSError:
        missing.append("factory.py")
    if not os.path.isfile(os.path.join(root, "docs", "capital_engine",
                                       "EXECUTION_ADAPTER_CONTRACT.md")):
        missing.append("docs/capital_engine/EXECUTION_ADAPTER_CONTRACT.md")
    if missing:
        return RED, "G5 unmet: missing " + ", ".join(missing)
    return GREEN, "kill switch code present; execution adapter contract present"


def evaluate_class(root, letter, ladder=None, min_days=None, today=None):
    auth = find_authorization(root, letter, today)
    gates = {"G1": gate_g1(root, letter, min_days), "G2": gate_g2(root, letter),
             "G3": gate_g3(root, letter, ladder, auth), "G4": gate_g4(root, letter, today),
             "G5": gate_g5(root)}
    statuses = [s for s, _ in gates.values()]
    if letter == "C":
        verdict, reason = RED, C_REASON
    elif RED in statuses:
        verdict = RED
        reason = "unmet: " + ", ".join(k for k, (s, _) in gates.items() if s == RED)
    elif AMBER in statuses:
        verdict = AMBER
        reason = "all met except " + ", ".join(k for k, (s, _) in gates.items() if s == AMBER)
    else:
        verdict, reason = GREEN, "all five gates met (a human still acts)"
    return dict(verdict=verdict, reason=reason, gates=gates)


def evaluate(root=REPO_ROOT, ladder=None, min_days=None, today=None):
    return {c: evaluate_class(root, c, ladder, min_days, today) for c in CLASSES}


def summary_lines(result):
    return {c: f"{r['verdict']} -- {r['reason']}" for c, r in result.items()}


def format_report(result):
    L = ["=== Capital activation gates (read-only; prints only, never acts) ==="]
    for c, r in result.items():
        L += ["", f"Class {c}: {r['verdict']}  ({r['reason']})"]
        for k, (status, why) in r["gates"].items():
            L.append(f"  {k} {GATE_NAMES[k]:<24}{status:<6} {why}")
    L += ["", "RED anywhere = no real money. GREEN is not an action: a human still acts."]
    return "\n".join(L)


def main(argv=None):
    print(format_report(evaluate()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
