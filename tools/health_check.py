"""
STRATEGY FACTORY - deterministic repo health check
====================================================
Purpose: replace repeated ad-hoc reasoning (a session manually re-deriving
"is the ledger missing anything, does state.json agree with itself") with
a single script that answers those exact questions every time, the same
way, for free. This exists because of a real incident: P0-3's
nifty_benchmark contestant sat merged in code but silently absent from
the live ledger for a full day before anyone happened to check by hand.
A script like this, run routinely, would have caught it on day one instead.

Every check here is PURE CODE -- no LLM judgment required to run it. A
session (interactive or Routine-fired) should run this FIRST, before
spending any tokens manually re-deriving the same facts via file reads.
Findings still need a human or an LLM session to decide what to DO about
them -- this script only detects, never fixes.

USAGE:  python tools/health_check.py [path/to/ledger.json] [path/to/state.json]
        python tools/health_check.py --live
        python tools/health_check.py --profile NAME [--live]     (CE-1-04)
--profile selects an asset-class profile (profiles/NAME.json). The default,
equity_nse, is today's behaviour and reads factory_state/; any other profile
reads factory_state/NAME/ (same layout factory.py writes). The repo-level
checks (state.json, CLAUDE.md hash, bug_log, equity profile integrity) run
only for the default profile -- they are not per-class.
Exit code 0 = no findings, 1 = findings exist (useful for CI/scripting).

--live fetches factory_state/ledger.json and .autonomous/state.json fresh
from main's raw GitHub content instead of reading the local checkout.
Added 2026-08-26 after a real recurring mistake: an interactive session's
local checkout tracks the WORKING BRANCH, but ledger.json is updated only
on main by factory.yml's daily cron -- so a plain local run here reliably
reports a stale/false "registry drift" warning that isn't real on main.
Every Routine prompt already says "fetch fresh, don't trust a stale local
copy" in English each time; this flag does that fetch in code instead, so
it stops needing to be re-said (and re-forgotten) every firing.
"""
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

RAW_BASE = "https://raw.githubusercontent.com/Hetlife/strategy-factory/main"


def fetch_live_json(repo_relative_path, timeout=15):
    """Fetches a file fresh from main via GitHub raw content. Returns the
    parsed JSON, or raises with a clear message on any failure (network,
    404, bad JSON) rather than letting a session guess at a stack trace."""
    url = f"{RAW_BASE}/{repo_relative_path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        raise RuntimeError(
            f"--live fetch failed for {url}: {e}. Falling back to a local "
            f"path won't give a trustworthy answer for this check -- fix "
            f"the network issue or fall back to explicit local paths "
            f"knowing they may be stale.") from e


def fetch_live_json_optional(repo_relative_path, timeout=15):
    """Like fetch_live_json, but a 404 (the file does not exist on main) returns
    None instead of raising. Any other failure still raises RuntimeError."""
    try:
        return fetch_live_json(repo_relative_path, timeout=timeout)
    except RuntimeError as e:
        cause = e.__cause__
        if isinstance(cause, urllib.error.HTTPError) and cause.code == 404:
            return None
        raise


def state_dir_rel(profile):
    """Repo-relative state dir for a profile (mirrors factory.STATE_DIR)."""
    from profiles import DEFAULT_PROFILE
    return "factory_state" if profile == DEFAULT_PROFILE else f"factory_state/{profile}"


def _ledger_last_update_date(ledger_data):
    """Newest date recorded in any contestant's history -- i.e. the last day
    an update() run actually executed and committed. ledger.json has no
    top-level timestamp, so contestant history is the honest source for
    this. Returns None if nothing dated is present (a brand-new ledger, or
    a malformed one) -- callers must handle that rather than assume a date.
    Deliberately tolerant of odd/short history rows: a monitoring helper
    must never be the thing that raises."""
    dates = []
    for c in (ledger_data.get("contestants") or {}).values():
        if not isinstance(c, dict):
            continue
        hist = c.get("history") or []
        if not hist:
            continue
        row = hist[-1]
        if isinstance(row, (list, tuple)) and row:
            dates.append(str(row[0]))
        elif isinstance(row, dict) and row.get("date"):
            dates.append(str(row["date"]))
    return max(dates) if dates else None


def _history_dates(contestant):
    """Dates of one contestant's history rows, tolerant of odd rows."""
    out = []
    for row in (contestant.get("history") or []) if isinstance(contestant, dict) else []:
        if isinstance(row, (list, tuple)) and row:
            out.append(str(row[0]))
        elif isinstance(row, dict) and row.get("date"):
            out.append(str(row["date"]))
    return out


def _utc_today():
    return datetime.datetime.now(datetime.timezone.utc).date()


def _last_weekday_on_or_before(day):
    """Simple NSE-calendar proxy: Sat/Sun roll back to Friday. No holiday list."""
    while day.weekday() >= 5:
        day -= datetime.timedelta(days=1)
    return day


def _missing_ledger_finding(profile, enabled, where):
    if enabled:
        return ("warning", f"[{profile}] profile is ENABLED but no ledger exists "
                f"at {where} -- its daily update has never produced one")
    return ("info", f"[{profile}] profile is disabled and has no ledger at "
            f"{where} -- nothing to check yet")


def check_stale_ledger(profile, ledger_data=None, today=None, profiles_dir=None,
                       root=None):
    """CE-1-04: is the newest history date recent enough for this profile?

    Weekday profiles: warn if the last recorded date is more than 4 calendar
    days older than the last NSE weekday (Sat/Sun roll back to Friday; no
    holiday list, so a long weekend is tolerated, a dead cron is not).
    Weekend profiles (trades_weekends true): warn if older than 2 calendar days
    from today. A ledger that is absent: info for a DISABLED profile (nothing
    has run yet, by design), warning for an ENABLED one. Pass ledger_data to
    skip the local read (e.g. from --live). Silent when fresh."""
    from profiles import load_profile
    prof = load_profile(profile, profiles_dir)
    enabled = prof.get("enabled") is True
    weekend = prof.get("trades_weekends") is True
    if ledger_data is None:
        path = os.path.join(root or REPO_ROOT, state_dir_rel(profile), "ledger.json")
        if not os.path.exists(path):
            return [_missing_ledger_finding(profile, enabled, path)]
        ledger_data = json.load(open(path))
    last = _ledger_last_update_date(ledger_data)
    if not last:
        return [("warning" if enabled else "info",
                 f"[{profile}] ledger has no dated contestant history")]
    try:
        last_d = datetime.date(*map(int, last.split("-")))
    except (ValueError, TypeError):
        return [("warning", f"[{profile}] ledger's newest history date {last!r} "
                            f"is not a YYYY-MM-DD date")]
    today = today or _utc_today()
    if weekend:
        age = (today - last_d).days
        if age > 2:
            return [("warning", f"[{profile}] last ledger date {last} is {age} "
                     f"days old (weekend profile trades every day; limit 2)")]
        return []
    ref = _last_weekday_on_or_before(today)
    age = (ref - last_d).days
    if age > 4:
        return [("warning", f"[{profile}] last ledger date {last} is {age} "
                 f"calendar days behind the last NSE weekday {ref} (limit 4) "
                 f"-- the daily update may have stopped")]
    return []


def check_duplicate_dates(profile, ledger_data=None, root=None):
    """CE-1-04: the same date appearing twice in one contestant's history.
    equity_nse's ledger already carries historical duplicates; cleaning them
    is a separate owner decision, so for the default profile this is INFO
    with the counts. Any other profile has no such history, so a duplicate
    there is a WARNING. Silent when there are none."""
    from profiles import DEFAULT_PROFILE
    if ledger_data is None:
        path = os.path.join(root or REPO_ROOT, state_dir_rel(profile), "ledger.json")
        if not os.path.exists(path):
            return []
        ledger_data = json.load(open(path))
    pairs = 0
    names = []
    for name, c in (ledger_data.get("contestants") or {}).items():
        counts = {}
        for d in _history_dates(c):
            counts[d] = counts.get(d, 0) + 1
        dup = sum(n - 1 for n in counts.values() if n > 1)
        if dup:
            pairs += dup
            names.append(name)
    if not pairs:
        return []
    msg = (f"[{profile}] {pairs} duplicate history row(s) across "
           f"{len(names)} contestant(s): {', '.join(sorted(names)[:5])}"
           f"{', ...' if len(names) > 5 else ''}")
    if profile == DEFAULT_PROFILE:
        return [("info", msg + ". Known historical duplicates; cleanup is the "
                 "owner's call, nothing to fix here.")]
    return [("warning", msg + ". A non-default profile should never have these.")]


def check_registry_drift(ledger_path=None, ledger_data=None):
    """Catches the exact bug class found 2026-08-25: a seed_registry() key
    that exists in code but never made it into an already-existing ledger,
    because load_state() only seeds a ledger that doesn't exist yet.
    NOTE: as of the fix in load_state(), this drift self-heals on the next
    update() -- this check exists to catch it BEFORE that, or to catch a
    similar future gap in some other part of the pipeline.

    Pass ledger_data (an already-loaded dict, e.g. from --live) to skip the
    local-file read entirely -- see fetch_live_json()."""
    findings = []
    if ledger_data is None:
        if not os.path.exists(ledger_path):
            return [("info", f"no ledger.json found at {ledger_path} -- "
                              "skipping registry-drift check (nothing to check yet)")]
        ledger_data = json.load(open(ledger_path))
    import factory
    seed_keys = set(factory.seed_registry().keys())
    ledger = ledger_data
    live_keys = set(ledger.get("registry", {}).keys())
    missing = seed_keys - live_keys
    if missing:
        last = _ledger_last_update_date(ledger_data)
        if last:
            detail = (
                f"The ledger's last update() was {last}. BENIGN if that date "
                f"is BEFORE these keys reached main -- load_state() backfills "
                f"them on the next update() run, so it clears itself. A REAL "
                f"BUG if an update() has run since they reached main and they "
                f"are STILL missing, because that means the backfill silently "
                f"failed. To tell which: compare {last} against the date those "
                f"keys were merged to main. Do not reflexively dismiss this "
                f"without doing that check.")
        else:
            detail = (
                "The ledger has no dated contestant history, so this check "
                "cannot tell whether an update() has run since these keys "
                "reached main. That is itself unusual for a ledger that has "
                "been trading -- treat an undated ledger as worth a human "
                "look rather than assuming the drift is benign.")
        findings.append(("warning",
            f"seed_registry() defines {sorted(missing)} but the ledger's "
            f"registry doesn't have them. {detail}"))
    orphans = live_keys - seed_keys
    # orphans are EXPECTED (bred/evolved children aren't in seed_registry) --
    # only flag if something looks like a seed-style name with no lineage,
    # which would suggest an actual naming mismatch rather than a real child.
    contestants = ledger.get("contestants", {})
    for name in sorted(orphans):
        c = contestants.get(name, {})
        if c and not c.get("lineage"):
            findings.append(("info",
                f"'{name}' is in the ledger's registry/contestants but not "
                f"in current seed_registry(), and has no lineage recorded -- "
                f"probably just an older seed name that was since removed "
                f"from seed_registry(), not necessarily a bug. Worth a human "
                f"glance if it's unexpected."))
    return findings


def check_state_json_wellformed(state_path):
    findings = []
    if not os.path.exists(state_path):
        return [("error", f"state.json not found at {state_path}")]
    state = json.load(open(state_path))
    for item in state.get("queue", []):
        for required in ("id", "priority", "status", "summary"):
            if required not in item:
                findings.append(("error",
                    f"queue item missing required field '{required}': "
                    f"{item.get('id', '<no id>')}"))
        commit = item.get("commit", "")
        if commit and not re.match(r"^([0-9a-f]{7,40}|n/a.*)$", commit):
            findings.append(("warning",
                f"queue item '{item.get('id')}' has a commit field that "
                f"doesn't look like a real sha or an explicit n/a-* tag: "
                f"'{commit}' -- possibly a typo."))
    return findings


def check_claude_md_sha1(state_path, claude_md_path):
    findings = []
    if not (os.path.exists(state_path) and os.path.exists(claude_md_path)):
        return findings
    state = json.load(open(state_path))
    recorded = state.get("claude_md_sha1", "")
    actual = hashlib.sha1(open(claude_md_path, "rb").read()).hexdigest()
    # historical entries in this project have sometimes carried one stray
    # leading/trailing char -- compare on the real 40-char hex substring.
    recorded_clean = re.sub(r"[^0-9a-f]", "", recorded)[-40:]
    if recorded_clean != actual:
        findings.append(("warning",
            f"state.json's claude_md_sha1 ({recorded}) doesn't match "
            f"CLAUDE.md's actual sha1 ({actual}) -- CLAUDE.md was edited "
            f"without updating the recorded hash, or vice versa."))
    return findings


def check_bug_log_state_consistency(bug_log_path, state_path):
    """Lightweight heuristic: an id that state.json's queue marks as
    done/closed/cleared shouldn't still appear under bug_log.md's OPEN
    section header. String-matching, not semantic -- false negatives are
    expected and fine, this is a cheap tripwire, not a proof."""
    findings = []
    if not (os.path.exists(bug_log_path) and os.path.exists(state_path)):
        return findings
    state = json.load(open(state_path))
    resolved_ids = {
        item["id"] for item in state.get("queue", [])
        if any(tag in item.get("status", "")
               for tag in ("done", "cleared", "closed", "fixed"))
    }
    text = open(bug_log_path).read()
    open_section = text.split("## FIXED")[0] if "## FIXED" in text else text
    for rid in resolved_ids:
        # only meaningful for ids that look like they'd appear verbatim
        if rid in open_section and "## OPEN" in open_section:
            # allow it if that exact line is also tagged CLOSED/FIXED nearby
            idx = open_section.find(rid)
            nearby = open_section[max(0, idx - 80):idx]
            if "CLOSED" not in nearby and "FIXED" not in nearby:
                findings.append(("info",
                    f"state.json marks '{rid}' as resolved, but bug_log.md's "
                    f"OPEN section still mentions it without a CLOSED/FIXED "
                    f"tag nearby -- worth a human glance, may just be a "
                    f"historical mention, not a real contradiction."))
    return findings


def check_phantom_days(market_log_path=None, log_data=None, macro=None):
    """CE-0-04: list recorded days that look phantom -- at least
    factory.PHANTOM_UNCHANGED_FRACTION of NON-macro tickers at exactly 0.0
    return (same rule update() now applies, same threshold as
    tools/detect_phantom_days.py). INFORMATION ONLY: returns a single
    'warning' (never an error) naming the dates. The guard stops NEW phantom
    days; historical ones stay in the record (cleanup is Het's call), so this
    keeps reporting them. Pass log_data to skip the local-file read, macro to
    use a profile's own MACRO_PROXIES (default: factory's, i.e. the active
    FACTORY_PROFILE; CE-1-04)."""
    import factory
    macro = factory.MACRO_PROXIES if macro is None else macro
    if log_data is None:
        if not market_log_path or not os.path.exists(market_log_path):
            return []
        log_data = json.load(open(market_log_path))
    phantom = []
    for date in sorted(log_data):
        day = log_data[date]
        if not isinstance(day, dict):
            continue
        rows = [v for t, v in day.items() if t not in macro
                and isinstance(v, dict) and "ret" in v]
        if len(rows) < 10:        # too few tickers to judge (detector's rule)
            continue
        frac = sum(1 for v in rows if v["ret"] == 0.0) / len(rows)
        if frac >= factory.PHANTOM_UNCHANGED_FRACTION:
            phantom.append(f"{date} ({frac:.0%})")
    if not phantom:
        return []
    return [("info",
        f"market_log.json has {len(phantom)} phantom day(s) (>= "
        f"{factory.PHANTOM_UNCHANGED_FRACTION:.0%} of tickers unchanged): "
        f"{', '.join(phantom)}. Information only -- history is never "
        f"rewritten; see tools/detect_phantom_days.py and CE-0-04.")]


def check_profile_integrity(profile_dir=None):
    """CE-1-02: profiles/equity_nse.json must (a) carry none of rules/ladder/
    cost_per_side and (b) when FACTORY_PROFILE is unset/equity_nse, hold
    exactly the values factory.py runs with. Errors, not info: a drifted
    equity profile silently changes the live arena."""
    from profiles import load_profile, ProfileError, DEFAULT_PROFILE
    path = os.path.join(profile_dir or os.path.join(REPO_ROOT, "profiles"),
                        DEFAULT_PROFILE + ".json")
    try:
        profile = load_profile(DEFAULT_PROFILE, os.path.dirname(path))
    except ProfileError as e:
        return [("error", f"profile integrity: {e}")]
    if os.environ.get("FACTORY_PROFILE", DEFAULT_PROFILE) != DEFAULT_PROFILE:
        return []         # factory's constants belong to another profile here
    import factory
    findings = []
    for name in ("UNIVERSE", "MACRO_PROXIES", "BENCHMARK", "STATE_DIR",
                 "VARIABLE_COST_PER_SIDE", "DP_CHARGE_PER_SCRIP", "STCG_RATE",
                 "LTCG_RATE", "LTCG_EXEMPTION_PER_YEAR"):
        if name not in profile:
            findings.append(("error", f"{DEFAULT_PROFILE}.json is missing {name}"))
        elif profile[name] != getattr(factory, name):
            findings.append(("error",
                f"{DEFAULT_PROFILE}.json {name} differs from factory.{name}"))
    return findings


def run_all(ledger_path=None, state_path=None, live=False, profile=None,
            profiles_dir=None, root=None, today=None):
    """Every check for one profile (default equity_nse = the pre-CE-1-04
    behaviour). Per-profile checks: registry drift, stale ledger, duplicate
    dates, phantom days. Repo-level checks run for the default profile only."""
    from profiles import load_profile, DEFAULT_PROFILE
    profile = profile or DEFAULT_PROFILE
    root = root or REPO_ROOT
    prof = load_profile(profile, profiles_dir)
    is_default = profile == DEFAULT_PROFILE
    rel = state_dir_rel(profile)
    ledger_path = ledger_path or os.path.join(root, rel, "ledger.json")
    state_path = state_path or os.path.join(root, ".autonomous", "state.json")
    bug_log_path = os.path.join(root, ".autonomous", "bug_log.md")
    claude_md_path = os.path.join(root, "CLAUDE.md")
    macro = prof.get("MACRO_PROXIES")
    enabled = prof.get("enabled") is True

    findings = []
    log_data = None
    if live:
        ledger_data = fetch_live_json_optional(f"{rel}/ledger.json")
        try:
            log_data = fetch_live_json_optional(f"{rel}/market_log.json")
        except RuntimeError as e:
            findings.append(("info", f"phantom-day check skipped: {e}"))
    else:
        ledger_data = json.load(open(ledger_path)) if os.path.exists(ledger_path) else None
        mlp = os.path.join(root, rel, "market_log.json")
        log_data = json.load(open(mlp)) if os.path.exists(mlp) else None

    if ledger_data is None:
        where = f"{rel}/ledger.json on main" if live else ledger_path
        findings.append(_missing_ledger_finding(profile, enabled, where))
    else:
        import factory
        if is_default or factory.FACTORY_PROFILE == profile:
            findings += check_registry_drift(ledger_data=ledger_data)
        else:
            findings.append(("info", f"[{profile}] registry-drift check skipped: "
                "factory.seed_registry() is bound to FACTORY_PROFILE="
                f"{factory.FACTORY_PROFILE}; run with that env var set"))
        findings += check_stale_ledger(profile, ledger_data=ledger_data, today=today,
                                       profiles_dir=profiles_dir, root=root)
        findings += check_duplicate_dates(profile, ledger_data=ledger_data)
    if log_data is not None:
        findings += check_phantom_days(log_data=log_data, macro=macro)
    # state.json/CLAUDE.md/bug_log.md aren't subject to the same
    # branch-vs-main drift (they're not written by factory.yml's
    # main-only cron) -- local checkout is a trustworthy source for these
    # regardless of --live. Repo-level, not per-class: default profile only.
    if is_default:
        findings += check_profile_integrity()
        findings += check_state_json_wellformed(state_path)
        findings += check_claude_md_sha1(state_path, claude_md_path)
        findings += check_bug_log_state_consistency(bug_log_path, state_path)
    return findings


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Deterministic repo/ledger health check")
    ap.add_argument("ledger", nargs="?")
    ap.add_argument("state", nargs="?")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--profile", default=None, help="asset-class profile (default equity_nse)")
    args = ap.parse_args(argv)
    if args.live:
        print("health_check: --live mode, fetching factory_state/ledger.json fresh from main...")
    try:
        results = run_all(args.ledger, args.state, live=args.live, profile=args.profile)
    except (RuntimeError, ValueError) as e:     # ProfileError is a ValueError
        print(f"[ERROR] {e}")
        return 2
    if not results:
        print("health_check: no findings.")
        return 0
    for level, msg in results:
        print(f"[{level.upper()}] {msg}")
    # info-only findings are context, not failures: the 15-minute supervisor
    # and the ce-workorder orient step treat exit 1 as "something is wrong".
    if all(level == "info" for level, _ in results):
        print("health_check: informational findings only, nothing to fix.")
        return 0
    return 1


def _bind_factory_profile(argv):
    """factory.py reads FACTORY_PROFILE at import and seed_registry() depends
    on it, so a CLI run for another profile must set it BEFORE any import of
    factory. Only done for a real CLI run, never when main() is called from
    a test or another module."""
    for i, a in enumerate(argv):
        name = (a.split("=", 1)[1] if a.startswith("--profile=")
                else argv[i + 1] if a == "--profile" and i + 1 < len(argv) else None)
        if name and name != "equity_nse":
            os.environ.setdefault("FACTORY_PROFILE", name)


if __name__ == "__main__":
    _bind_factory_profile(sys.argv[1:])
    sys.exit(main())
