"""Seeded synthetic price panel for the golden-master harness (CE-1-01).

Pure numpy/pandas. No network. Same seed -> same panel, bit for bit: returns
come from numpy's PCG64 `default_rng`, prices are cumulative products (no
exp/log, so no libm differences between platforms) and are ROUNDED to 2
decimals, so the inputs handed to factory.py are identical everywhere.
"""
import numpy as np
import pandas as pd

DEFAULT_SEED = 20261004


def make_panel(tickers, n_history=300, n_new=40, seed=DEFAULT_SEED,
               shocks=None, benchmark="^NSEI",
               history_end="2026-10-02", first_new="2026-10-05"):
    """Return a business-day price DataFrame (n_history + n_new rows).

    Rows 0..n_history-1 are "history"; the next n_new rows are the rows the
    harness feeds one per update() cycle (new row k has index n_history + k).

    shocks: {k: {ticker: daily_return}} -- overrides that ticker's return on
    the k-th NEW row (k = 0..n_new-1), so signals (event_drift, input_cost)
    can be forced to fire deterministically.
    """
    tickers = sorted(tickers)
    rng = np.random.default_rng(seed)
    n = n_history + n_new
    dates = pd.bdate_range(end=history_end, periods=n_history).append(
        pd.bdate_range(start=first_new, periods=n_new))
    # draw in sorted-ticker order so adding a ticker never reshuffles the rest
    rets = np.empty((n, len(tickers)))
    start = np.empty(len(tickers))
    for j, t in enumerate(tickers):
        vol = 0.008 if t == benchmark else 0.012
        rets[:, j] = rng.normal(0.0003, vol, size=n)
        start[j] = round(float(rng.uniform(50.0, 500.0)), 2)
    col = {t: j for j, t in enumerate(tickers)}
    for k, d in (shocks or {}).items():
        for t, r in d.items():
            rets[n_history + k, col[t]] = r
    levels = start * np.cumprod(1.0 + rets, axis=0)
    return pd.DataFrame(np.round(levels, 2), index=dates, columns=tickers)
