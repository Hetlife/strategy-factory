"""CE-1-03: print the enabled asset-class profiles as a JSON list (stdlib only).

Used by .github/workflows/factory.yml to build its job matrices.

    python tools/list_enabled_profiles.py             # all enabled profiles
    python tools/list_enabled_profiles.py --weekday   # trades_weekends is not true
    python tools/list_enabled_profiles.py --weekend   # trades_weekends is true

A profile is enabled only if its JSON has "enabled": true (exactly). Output is
a compact, sorted JSON list on one line, e.g. ["equity_nse"], so it can be fed
straight to fromJSON() in a workflow. An unreadable profile file is a hard
error (exit 1): silently dropping it would silently stop that class's updates.
"""
import argparse
import json
import os
import sys

DEFAULT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "profiles")


def list_profiles(profiles_dir=DEFAULT_DIR, mode=None):
    """Sorted names of enabled profiles; mode is None, "weekday" or "weekend"."""
    names = []
    for fname in sorted(os.listdir(profiles_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(profiles_dir, fname)
        with open(path) as fh:
            prof = json.load(fh)
        if not isinstance(prof, dict):
            raise ValueError(f"{path}: profile must be a JSON object")
        if prof.get("enabled") is not True:
            continue
        weekend = prof.get("trades_weekends") is True
        if mode == "weekend" and not weekend:
            continue
        if mode == "weekday" and weekend:
            continue
        names.append(fname[:-len(".json")])
    return sorted(names)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--weekend", action="store_true", help="only trades_weekends profiles")
    grp.add_argument("--weekday", action="store_true", help="only non-weekend profiles")
    ap.add_argument("--dir", default=DEFAULT_DIR, help="profiles directory")
    args = ap.parse_args(argv)
    mode = "weekend" if args.weekend else "weekday" if args.weekday else None
    try:
        names = list_profiles(args.dir, mode)
    except (OSError, ValueError) as e:
        print(f"list_enabled_profiles: {e}", file=sys.stderr)
        return 1
    print(json.dumps(names, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
