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
