"""
STRATEGY FACTORY - advisor training layer
==========================================
Backward-looking research layer that pulls historical price data, backtests
a wide parameter grid per strategy family through the SAME sig_* functions
factory.py uses live, and scores every candidate with three independent
"advisor" heuristics (an ensemble, not a single grid-search winner):

  * sharpe_advisor       - raw full-period risk-adjusted return
  * robustness_advisor   - min(first-half, second-half) Sharpe, so a
                            parameter set that only worked in one regime
                            scores poorly (see 03_learnings_and_suggestions
                            lesson #3 - the stat-arb regime-break collapse)
  * cost_efficiency_advisor - net return per round trip, so a high-turnover
                            parameter set that only wins before costs scores
                            poorly (lesson #2)

Output is a ranked "parameter bank" per (strategy family, sector), written
to factory_state/parameter_bank.json. factory.py's report() step blends a
bank entry with a live contestant's own current parameters -- weighted by
factory_state/advisor_state.json's self-tuning trust_weight -- to propose a
mutated replacement for a paper-tier (rung 0) contestant that isn't
ranking in the tournament's overall top 10. This is a deliberate, explicit
override of Law 1 (train parameters from historical data) authorized by
Het; see maintenance_notes for the design conversation. It never touches a
contestant already on a real-money rung -- those still only evolve through
factory.py's existing spawn_children() breeding-on-promotion path.

USAGE:  python advisors.py train    (monthly, via Actions cron)
State lives in ./factory_state/parameter_bank.json
"""
import json, os, itertools
from datetime import datetime, timezone
import numpy as np
import pandas as pd

from factory import (STATE_DIR, UNIVERSE, ALL_TICKERS, COST_PER_SIDE,
                      IMPLS, seed_registry)

BANK_PATH = os.path.join(STATE_DIR, "parameter_bank.json")
TRAIN_PERIOD = "5y"          # depth of history used for advisor training
TOP_N_PER_BUCKET = 5         # how many ranked candidates to keep per family/sector

# ---------------- parameter grids (mechanism-bounded, not unbounded scans) --
# Every grid stays inside the same mechanism-based ranges the seed registry
# already uses (see 02_architecture.txt) -- advisors rank within a sane
# hypothesis space, they don't invent a new mechanism.
def build_grid():
    grid = []  # list of (family, sector, name_hint, params)
    for sector, leader in [("cement", "ULTRACEMCO.NS"), ("infra", "LT.NS"),
                            ("steel", "TATASTEEL.NS")]:
        for threshold in (0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08):
            for hold in (2, 3, 4, 5):
                grid.append(("event_drift", sector, dict(
                    fn="event_drift", sector=sector, leader=leader,
                    threshold=threshold, hold=hold)))
    for sector in ("cement", "infra", "pipes_tiles"):
        for lookback in (20, 30, 40, 60, 90, 120):
            grid.append(("momentum", sector, dict(
                fn="momentum", sector=sector, lookback=lookback, top_frac=0.34)))
    for sector, proxy in [("cement", "TATASTEEL.NS")]:
        for lb in (10, 15, 20, 30, 40):
            for drop in (-0.03, -0.04, -0.05, -0.06, -0.08):
                grid.append(("input_cost", sector, dict(
                    fn="input_cost", sector=sector, proxy=proxy, lb=lb, drop=drop)))
    return grid

def fetch_history():
    import yfinance as yf
    px = yf.download(ALL_TICKERS, period=TRAIN_PERIOD, auto_adjust=True,
                      progress=False)["Close"]
    return px.dropna(how="all").ffill()

# ---------------- offline backtest (mirrors factory.py's no-lookahead order) --
def backtest(px, params, warmup=130):
    """Walk the full history exactly like update() does: yesterday's target
    positions realize P&L against today's return, costs charged on turnover.
    Returns a daily net-return series (post-cost)."""
    fn = IMPLS[params["fn"]]
    rets = px.pct_change()
    positions = {}
    daily_net = []
    for i in range(warmup, len(px)):
        window = px.iloc[:i + 1]
        today_ret = rets.iloc[i]
        day_ret = sum(w * today_ret.get(t, 0.0) for t, w in positions.items())
        try:
            targets = fn(window, params)
        except Exception:
            targets = {}
        tickers = set(positions) | set(targets)
        turn = sum(abs(targets.get(t, 0) - positions.get(t, 0)) for t in tickers)
        net = day_ret - turn * COST_PER_SIDE
        daily_net.append(net)
        positions = targets
    return pd.Series(daily_net)

def sharpe(returns):
    if len(returns) < 20:
        return -99.0
    mean, std = returns.mean(), returns.std()
    if std < 1e-9:
        return -99.0
    return float(mean / std * np.sqrt(252))

def score_candidate(net_returns):
    """Three independent advisor heuristics -> one ensemble score."""
    n = len(net_returns)
    half = n // 2
    first_half, second_half = net_returns.iloc[:half], net_returns.iloc[half:]

    sharpe_advisor = sharpe(net_returns)
    robustness_advisor = min(sharpe(first_half), sharpe(second_half))
    n_trades = max(int((net_returns.abs() > 1e-6).sum()), 1)
    cost_efficiency_advisor = float(net_returns.sum() / n_trades) * 1000  # bps/trade

    return dict(sharpe=round(sharpe_advisor, 3),
                robustness=round(robustness_advisor, 3),
                cost_efficiency=round(cost_efficiency_advisor, 4))

def ensemble_rank(candidates):
    """Rank-average the three advisor scores (each advisor votes by rank,
    not raw magnitude, so no single heuristic's scale dominates)."""
    df = pd.DataFrame(candidates)
    for col in ("sharpe", "robustness", "cost_efficiency"):
        df[f"rank_{col}"] = df[col].rank(ascending=False, method="average")
    df["ensemble_rank"] = df[["rank_sharpe", "rank_robustness",
                               "rank_cost_efficiency"]].mean(axis=1)
    return df.sort_values("ensemble_rank")

def train():
    print("Advisor training: downloading historical prices "
          f"(period={TRAIN_PERIOD})...")
    px = fetch_history()
    grid = build_grid()
    print(f"Backtesting {len(grid)} parameter candidates across "
          f"{len({(f, s) for f, s, _ in grid})} (family, sector) buckets...")

    buckets = {}
    for fn, sector, params in grid:
        net = backtest(px, params)
        if net.empty:
            continue
        scores = score_candidate(net)
        buckets.setdefault((fn, sector), []).append({**scores, "params": params})

    bank = {}
    for (fn, sector), candidates in buckets.items():
        ranked = ensemble_rank(candidates).head(TOP_N_PER_BUCKET)
        bank.setdefault(fn, {})[sector] = [
            dict(params=row["params"], sharpe=row["sharpe"],
                 robustness=row["robustness"],
                 cost_efficiency=row["cost_efficiency"],
                 ensemble_rank=round(float(row["ensemble_rank"]), 2))
            for _, row in ranked.iterrows()
        ]

    os.makedirs(STATE_DIR, exist_ok=True)
    out = dict(generated_at=datetime.now(timezone.utc).isoformat(),
               train_period=TRAIN_PERIOD, advisors=["sharpe", "robustness",
               "cost_efficiency"], bank=bank)
    json.dump(out, open(BANK_PATH, "w"), indent=1)
    print(f"Wrote {BANK_PATH}: "
          f"{sum(len(v) for v in bank.values())} (family, sector) buckets, "
          f"top {TOP_N_PER_BUCKET} candidates each.")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "train"
    {"train": train}[cmd]()
