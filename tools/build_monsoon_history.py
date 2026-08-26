"""Builds a HISTORICAL (not live) all-India monsoon rainfall departure
series from the free/open IMD subdivision data in data/raw/.

Deliberately writes to data/imd_rainfall_departure_historical.csv, NOT to
the live path (`imd_rainfall_departure.csv`, repo root) that
factory.py's sig_monsoon() actually reads for trading decisions.

Why the split path matters: this source data ends in 2017. If it were
dropped at the live path, sig_monsoon would forward-fill that last 2017
reading forever and silently trade on a 9-year-stale number as if it
were current -- worse than staying dormant. sig_monsoon should only go
live once a real *current* feed exists (Het: "then we will add real time
data" -- separate, future step). Until then this file is backtest/
research material only.

Method (kept simple, documented rather than hidden):
  - "All-India" monthly rainfall = simple mean across the 36 IMD
    subdivisions for that month (not IMD's official area-weighting --
    a documented approximation, not presented as IMD's own number).
  - Baseline "normal" = each calendar month's mean over 1971-2010
    (IMD's own standard climatology reference period).
  - departure_pct = (month's all-India value / that month's baseline
    - 1) * 100, one row per month, first-of-month dated.
"""
import pandas as pd
import os

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw",
                    "imd_subdivision_monthly_rainfall_1901_2017.csv")
OUT = os.path.join(os.path.dirname(__file__), "..", "data",
                    "imd_rainfall_departure_historical.csv")
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP",
          "OCT", "NOV", "DEC"]
BASELINE_YEARS = (1971, 2010)


def build():
    df = pd.read_csv(RAW)
    all_india = df.groupby("YEAR")[MONTHS].mean()

    baseline = all_india.loc[BASELINE_YEARS[0]:BASELINE_YEARS[1]].mean()

    rows = []
    for year, row in all_india.iterrows():
        for i, m in enumerate(MONTHS, start=1):
            if pd.isna(row[m]) or baseline[m] == 0:
                continue
            pct = (row[m] / baseline[m] - 1) * 100
            rows.append({"date": f"{year}-{i:02d}-01",
                         "rainfall_departure_pct": round(pct, 2)})

    out = pd.DataFrame(rows).sort_values("date")
    out.to_csv(OUT, index=False)
    print(f"Wrote {len(out)} rows to {OUT} "
          f"({out['date'].iloc[0]} to {out['date'].iloc[-1]})")
    return out


if __name__ == "__main__":
    build()
