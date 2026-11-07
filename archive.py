"""Data archive writers (CE-6-01). See docs/capital_engine/DATA_ARCHIVE.md.

GitHub is the system of record: these functions append to files under
<state_dir>/archive/, which the existing workflows already commit via
`git add factory_state`. stdlib + pandas only. Nothing here may ever change a
run's outcome -- callers go through safe().

  pulls/YYYY-MM.csv       vintage log of RAW (pre-ffill) closes, one row each
                          time a (panel_date, ticker) value is first seen or
                          changes (NaN counts as a value); append-only
  runs/YYYY-MM.jsonl      one JSON line per update/report run
  reports/YYYY-MM-DD.txt  full text of the weekly report (same day overwrites)
"""
import csv
import json
import math
import os

import pandas as pd

PULL_FIELDS = ["panel_date", "ticker", "close", "first_seen_utc", "pull_id"]


def _dir(state_dir, sub):
    path = os.path.join(state_dir, "archive", sub)
    os.makedirs(path, exist_ok=True)
    return path


def safe(fn, *args, **kwargs):
    """Call fn; on ANY exception print a warning and return None."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 -- the archive must never stop a run
        print(f"[archive warning] {getattr(fn, '__name__', 'archive call')} "
              f"failed: {type(e).__name__}: {e}")
        return None


def _is_nan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def _same(a, b):
    if _is_nan(a) and _is_nan(b):
        return True
    if _is_nan(a) or _is_nan(b):
        return False
    # one part in a billion: absorbs float noise between identical pulls, keeps every real revision
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=0.0)


def _load_latest(path):
    """{(panel_date, ticker): latest stored close or None} from one pulls file."""
    latest = {}
    if not os.path.exists(path):
        return latest
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            v = row.get("close", "")
            latest[(row["panel_date"], row["ticker"])] = float(v) if v != "" else None
    return latest


def record_pull(state_dir, raw, pulled_at, pull_id, keep_last=6):
    """Append changed/new values of the last `keep_last` rows of the raw Close
    panel to pulls/YYYY-MM.csv (month of the PANEL date). Returns rows written."""
    if raw is None or len(raw) == 0 or len(raw.columns) == 0:
        return 0
    tail = raw.iloc[-keep_last:]
    dates = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in tail.index]
    pdir = _dir(state_dir, "pulls")
    stored = {}
    for month in sorted({d[:7] for d in dates}):
        stored.update(_load_latest(os.path.join(pdir, month + ".csv")))
    by_month = {}
    cols = [str(c) for c in tail.columns]
    order = sorted(range(len(cols)), key=lambda i: cols[i])
    for d, values in zip(dates, tail.to_numpy(dtype=float)):
        for i in order:
            ticker, val = cols[i], values[i]
            val = None if pd.isna(val) else float(val)
            key = (d, ticker)
            if key in stored and _same(stored[key], val):
                continue
            by_month.setdefault(d[:7], []).append(
                [d, ticker, "" if val is None else repr(val), pulled_at, pull_id])
    written = 0
    for month, rows in by_month.items():
        path = os.path.join(pdir, month + ".csv")
        new_file = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, "a", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            if new_file:
                w.writerow(PULL_FIELDS)
            w.writerows(rows)
        written += len(rows)
    return written


def record_run(state_dir, record):
    """Append one JSON object (sorted keys) as a line in runs/YYYY-MM.jsonl."""
    month = str(record["ts_utc"])[:7]
    path = os.path.join(_dir(state_dir, "runs"), month + ".jsonl")
    with open(path, "a") as fh:
        fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def save_report(state_dir, text, day):
    """Write reports/<day>.txt (the same day overwrites)."""
    path = os.path.join(_dir(state_dir, "reports"), f"{day}.txt")
    with open(path, "w") as fh:
        fh.write(text)
