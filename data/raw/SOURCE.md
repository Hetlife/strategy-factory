# Source: imd_subdivision_monthly_rainfall_1901_2017.csv

Fetched (free, open) 2026-08-26 from:
https://raw.githubusercontent.com/dcsavinod/weather-and-rainfall-data-from-1901-to-2022/main/Rainfall_State_Analysis_India_1901_2017.csv

Community GitHub mirror of India Meteorological Department (IMD)
subdivision-wise monthly rainfall statistics — public government data,
redistributed. Columns: subdivision, year, monthly rainfall totals (mm)
Jan-Dec, seasonal aggregates, subdivision lat/long. Coverage: 1901-2017,
36 IMD subdivisions.

This sandbox's network policy blocks direct access to data.gov.in and the
IMD's own domains (mausam.imd.gov.in, imdpune.gov.in, indiadataportal.com)
— GitHub raw content is reachable, so this mirror was used instead. Not
verified against the IMD original byte-for-byte; treat as good-enough for
backtesting, not as an authoritative live feed.

Used by `tools/build_monsoon_history.py` — see that file and
`factory.py`'s `sig_monsoon` docstring for how (and how NOT) this feeds
the monsoon_cement contestant.
