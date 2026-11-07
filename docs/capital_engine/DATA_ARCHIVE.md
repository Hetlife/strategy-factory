# Data archive — where every pull and every run is stored (decision record, 2026-11-07)

**Decision: GitHub is the system of record, written by exactly one writer (the existing Actions runs). Lucy-den holds a read-only mirror. Not two writers.**

## Why not "write from both"
| | GitHub (the repo, written by Actions) | Lucy-den (the LucyOS host) |
|---|---|---|
| Runs when your PC is off or frozen | **Yes** (Lucy-den has had freezes, planning ISSUE-042) | No |
| Real internet / Yahoo access | Yes | Yes (home IP) |
| Versioned, tied to the ledger commit | **Yes** | Only if it mirrors git |
| Cost | Free | Free, but a live disk and one machine |
| Off-machine backup | **Yes, by definition** | Only via LucyOS backup (TR-2-02, not verified live) |
| Conflict risk | None with one writer | Two writers to one history = merge conflicts, a push credential on the host |
| LucyOS rule | C9: evidence subsystem lives in its repo | Anti-dup: no second source of truth |

## Layout (per profile; equity_nse uses `factory_state/`, others `factory_state/<profile>/`)
```
<STATE_DIR>/archive/pulls/YYYY-MM.csv     vintage log of RAW prices: one row each time a (date,ticker) close is first seen or changes (including NaN)
<STATE_DIR>/archive/runs/YYYY-MM.jsonl    one JSON line per update/report run, INCLUDING skipped, phantom-skipped, failed and no-change runs
<STATE_DIR>/archive/reports/YYYY-MM-DD.txt  the full text of each weekly report
```
`ledger.json` keeps being overwritten in place; its full history is the git history (one commit per run). The kill switch wins: a run stopped by `KILL` writes nothing.

## What a "vintage" pull row gives you
`panel_date,ticker,close,first_seen_utc,pull_id`. The raw pull BEFORE forward-filling is stored for the last 6 sessions, only when a value is new or changed, so a late posting or a Yahoo revision shows up as a second row for the same date. That is the evidence trail for the holes found on 2026-10-07 (R4) and the input to any later reconciliation against NSE bhavcopy.

## Size
About 115 tickers x a handful of changed values a day: roughly 5 KB a day, under 2 MB a year per profile, plus about 0.5 KB per run. The repo is 2.6 MB today; GitHub's practical limit is 1 GB.

## Lucy-den mirror (read-only)
LucyOS's nightly maintenance already runs `scripts/sync_project_evidence.py` (CE-5-02), which keeps a clone at `$AION_HOME/PROJECTS/strategy-factory/repo` and `git pull --ff-only` each night. That clone is the mirror. Gap: it was created with `--depth 1`, so it lacks old history. CE-6-03 makes it a full clone (the repo is tiny). Lucy-den also gets an off-GitHub backup for free if the LucyOS backup covers `$AION_HOME` (unverified: check `aion backup` config).

## Later, optional (needs your go-ahead, not built)
Lucy-den could fetch NSE's official end-of-day files (`BhavCopy_NSE_CM_...`, ~30-60 min after close) from its home IP as an independent source for reconciling Yahoo. NSE often blocks cloud IPs, so CE-6-02 first tests whether GitHub Actions can fetch them at all; if it can, no second writer is needed.
