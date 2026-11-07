# strategy-factory
Claude code for algo trading 

## Per-profile schedule (CE-1-03)

`.github/workflows/factory.yml` runs one job per enabled asset-class profile. A
small `discover` job runs `tools/list_enabled_profiles.py` to read
`profiles/*.json` and emit two matrices: weekday profiles (currently just
`equity_nse`, same crons, weekday guard and `Factory update` commit prefix as
before) and `trades_weekends` profiles, which run on a separate daily 02:30 UTC
cron with no weekday guard and are skipped cleanly while that list is empty. Each
matrix leg sets `FACTORY_PROFILE` and has its own concurrency group
(`<workflow>-<profile>`), so two profiles never race on the same commit.
Disabled profiles never appear in a matrix.

## Kill switch (CE-4-02)

A file named `factory_state/KILL` stops every write path in the engine:
`factory.py update`, `factory.py report` and `advisors.py train` each check for
it before touching anything, print `KILL SWITCH ACTIVE -- <your text>; no state
changed.` and exit. A non-default profile also stops on its own
`factory_state/<profile>/KILL` (that profile only). The workflows print the
switch status as their first step, and `tools/health_check.py` reports a
WARNING while the file exists.

**Pull it from a phone (no session or model needed):** open the repo in
GitHub's web UI on the `main` branch, go to `factory_state/`, tap Add file ->
Create new file, name it `KILL`, write a one-line reason in the body, and
commit directly to `main`. The next scheduled run does nothing.

**Release it:** open `factory_state/KILL` on `main` in the web UI, delete the
file, commit. The next run resumes normally.

## Data archive (CE-6-01)

Every `factory.py update` / `report` run leaves a record under
`<state dir>/archive/` (`factory_state/archive/` for `equity_nse`,
`factory_state/<profile>/archive/` otherwise), committed by the workflows'
existing `git add factory_state`. GitHub is the one writer; see
`docs/capital_engine/DATA_ARCHIVE.md` for why.

- `pulls/YYYY-MM.csv` -- raw (pre-forward-fill) closes of the last 6 sessions, one row each time a (date, ticker) value is first seen or changes (NaN included), so late postings and Yahoo revisions stay visible.
- `runs/YYYY-MM.jsonl` -- one JSON line per run: outcome (`recorded`, `skipped`, `failed`, `reported`, `error:<Name>`), phantom-skipped date, ticker/NaN counts, ledger hash, commit, run id, library versions.
- `reports/YYYY-MM-DD.txt` -- the full weekly report text.

A run stopped by `KILL` writes nothing. An archive failure only prints
`[archive warning] ...`; it never changes the run's output or exit code.
Code: `archive.py`, wired in by `factory.main()`; tests: `tests/test_archive.py`.
