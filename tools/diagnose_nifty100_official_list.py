"""
One-off diagnostic: does UNIVERSE["nifty100"] actually match NSE's own
official, currently-published Nifty 100 constituent list?

Origin: 2026-08-29, Het suggested using other GitHub repos as a resource
to help develop/optimize this project. Two community-maintained GitHub
CSV snapshots were tried first for the still-open "correct current
ticker for Tata Motors / LTIMindtree" question (see het_directives.md)
and both turned out to be stale (one lists MINDTREE.NS/NIITTECH.NS,
defunct for years; the other lists "MindTree Ltd." as a standalone
company, predating the Nov-2022 LTI-Mindtree merger). Rather than trust
a third community snapshot on faith, this goes to the actual primary
source: NSE publishes its own official index-constituent CSVs directly
at a stable, well-known archive URL
(https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv
-- confirmed via search, this is NSE's own domain, not a mirror).

This sandbox cannot reach nseindia.com (documented env fact, confirmed
via repeated real WebFetch attempts this session). This script is meant
to run on a GitHub Actions runner, which has real internet access. Uses
plain urllib (no new dependency) with a browser-like User-Agent, since
NSE's servers are known to reject requests without one.

Read-only. Prints findings. Never writes to seed_registry() or
UNIVERSE -- a session reviews the output and decides what, if anything,
to change, same as every other diagnostic in this project.

USAGE: python tools/diagnose_nifty100_official_list.py
"""
import csv
import io
import os
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import factory

NSE_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv"


def fetch_official_rows():
    """Returns {bare NSE symbol (no .NS suffix): company name} from NSE's
    own published Nifty 100 constituent CSV. Raises on any failure --
    callers must not silently treat a failed fetch as 'the list is empty'.
    Company name comes straight from NSE's own CSV column -- no second
    network call (e.g. to yfinance) needed just to identify a symbol."""
    req = urllib.request.Request(
        NSE_URL,
        headers={
            # NSE's servers reject requests with no / non-browser User-Agent.
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0 Safari/537.36"),
            "Accept": "text/csv,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8-sig")  # NSE CSVs often have a BOM
    reader = csv.DictReader(io.StringIO(raw))
    fields = reader.fieldnames or []
    if "Symbol" not in fields:
        raise ValueError(
            f"unexpected CSV format, columns were: {fields} -- NSE may "
            f"have changed the file layout, don't assume the symbol "
            f"column is still called 'Symbol'.")
    name_col = "Company Name" if "Company Name" in fields else None
    return {
        row["Symbol"].strip(): (row.get(name_col, "") or "").strip() if name_col else ""
        for row in reader if row.get("Symbol")
    }


def main():
    official_rows = fetch_official_rows()
    official = set(official_rows)
    print(f"Fetched {len(official)} symbols from NSE's official Nifty 100 list.\n")

    ours_with_ns = set(factory.UNIVERSE["nifty100"])
    ours_bare = {t[:-3] if t.endswith(".NS") else t for t in ours_with_ns}

    missing_from_ours = sorted(official - ours_bare)
    extra_in_ours = sorted(ours_bare - official)

    print(f"Our UNIVERSE['nifty100']: {len(ours_bare)} symbols")
    print(f"NSE's official list:      {len(official)} symbols\n")

    if missing_from_ours:
        print(f"IN NSE'S OFFICIAL LIST BUT NOT IN OURS ({len(missing_from_ours)}):")
        for s in missing_from_ours:
            name = official_rows.get(s, "")
            print(f"  {s}" + (f"  ({name})" if name else ""))
    else:
        print("Nothing in NSE's official list is missing from ours.")

    print()
    if extra_in_ours:
        print(f"IN OURS BUT NOT IN NSE'S CURRENT OFFICIAL LIST ({len(extra_in_ours)}):")
        for s in extra_in_ours:
            print(f"  {s}")
        print("(These may be stale/removed-from-index names, or names we "
              "kept for a real reason -- review, don't auto-remove.)")
    else:
        print("Nothing in ours is absent from NSE's current official list.")

    print()
    for name in ("TATAMOTORS", "LTIM", "LTIMINDTREE"):
        print(f"'{name}' in NSE's official list: {name in official}")

    if not missing_from_ours and not extra_in_ours:
        print("\nRESULT: exact match with NSE's official Nifty 100 list.")
    else:
        print(f"\nRESULT: {len(missing_from_ours)} missing + {len(extra_in_ours)} "
              f"extra vs NSE's official list -- review before changing UNIVERSE.")


if __name__ == "__main__":
    main()
