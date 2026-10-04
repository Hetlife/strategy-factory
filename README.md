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
