"""
STRATEGY FACTORY v2 - self-evolving edition (SevaaConnect Algo Project)
=======================================================================
A tournament of paper-traded strategies that improves itself by SELECTION:
  * seeds a grid of strategy variants automatically (18+ contestants)
  * auto-retires strategies that fail twice on paper
  * when a strategy earns real-capital rungs, auto-breeds "children" with
    neighbouring parameters - children start at paper and must earn promotion
  * never edits a live strategy (the #1 cause of curve-fit blowups)

USAGE:  python factory.py update   (daily, after market close - cron/Actions)
        python factory.py report   (weekly scoreboard + auto promotions)
State lives in ./factory_state/ledger.json
"""
import json, sys, os
import numpy as np
import pandas as pd

STATE_DIR = "factory_state"
COST_PER_SIDE = 0.0019            # STT + charges + slippage per side
BENCHMARK = "^NSEI"
MAX_CONTESTANTS = 40              # cap so the arena stays readable

UNIVERSE = {
    "cement": ["ULTRACEMCO.NS", "AMBUJACEM.NS", "ACC.NS", "SHREECEM.NS",
               "JKCEMENT.NS", "RAMCOCEM.NS", "DALBHARAT.NS"],
    "infra": ["LT.NS", "IRB.NS", "KNRCON.NS", "PNCINFRA.NS", "HGINFRA.NS"],
    "pipes_tiles": ["ASTRAL.NS", "SUPREMEIND.NS", "KAJARIACER.NS", "CERA.NS"],
    "steel": ["TATASTEEL.NS", "JSWSTEEL.NS", "JINDALSTEL.NS", "SAIL.NS"],
}
ALL_TICKERS = sorted({t for v in UNIVERSE.values() for t in v} | {BENCHMARK})

LADDER = [0, 10_000, 25_000, 50_000, 100_000]     # rupees per rung (0 = paper)
RULES = dict(min_days_on_rung=126, min_trades=10, min_expectancy=0.0005,
             max_drawdown=-0.12, min_sharpe=0.4, max_paper_failures=2)

# ---------------- strategy implementations (parametric) ----------------
def sig_event_drift(px, p):
    lead = px[p["leader"]].pct_change()
    recent = lead.iloc[-p["hold"]:]
    hit = recent[abs(recent) > p["threshold"]]
    if hit.empty:
        return {}
    d = float(np.sign(hit.iloc[-1]))
    lags = [t for t in UNIVERSE[p["sector"]] if t != p["leader"]]
    return {t: d / len(lags) for t in lags}

def sig_momentum(px, p):
    names = UNIVERSE[p["sector"]]
    mom = px[names].iloc[-p["lookback"]:].apply(lambda c: c.iloc[-1] / c.iloc[0] - 1)
    k = max(1, int(len(names) * p["top_frac"]))
    return {t: 1.0 / k for t in mom.nlargest(k).index}

def sig_input_cost(px, p):
    c = px[p["proxy"]].iloc[-p["lb"]:]
    if c.iloc[-1] / c.iloc[0] - 1 < p["drop"]:
        names = UNIVERSE[p["sector"]]
        return {t: 1.0 / len(names) for t in names}
    return {}

def sig_monsoon(px, p):
    if not os.path.exists(p["csv"]):
        return {}
    df = pd.read_csv(p["csv"], parse_dates=["date"]).set_index("date")
    s = df["rainfall_departure_pct"].asfreq("D", method="ffill").shift(p["lag"])
    if s.empty or pd.isna(s.iloc[-1]):
        return {}
    if s.iloc[-1] > p["thresh"]:
        names = UNIVERSE[p["sector"]]
        return {t: 1.0 / len(names) for t in names}
    return {}

IMPLS = {"event_drift": sig_event_drift, "momentum": sig_momentum,
         "input_cost": sig_input_cost, "monsoon": sig_monsoon}

def seed_registry():
    """Starting population: a small grid of variants per hypothesis."""
    reg = {}
    for sector, leader in [("cement", "ULTRACEMCO.NS"), ("infra", "LT.NS"),
                           ("steel", "TATASTEEL.NS")]:
        for thr in (0.03, 0.04, 0.05):
            reg[f"event_{sector}_t{int(thr*1000)}"] = dict(
                fn="event_drift", sector=sector, leader=leader,
                threshold=thr, hold=3)
    for sector in ("cement", "infra", "pipes_tiles"):
        for lb in (40, 60, 90):
            reg[f"mom_{sector}_lb{lb}"] = dict(
                fn="momentum", sector=sector, lookback=lb, top_frac=0.34)
    reg["input_cost_lag"] = dict(fn="input_cost", sector="cement",
                                 proxy="TATASTEEL.NS", lb=20, drop=-0.05)
    reg["monsoon_cement"] = dict(fn="monsoon", csv="imd_rainfall_departure.csv",
                                 lag=10, sector="cement", thresh=10.0)
    return reg

def spawn_children(name, params, registry):
    """Breed neighbour variants when a parent wins promotion. Children start
    on paper (rung 0) and must earn their own way up. Selection, not editing."""
    born = []
    def add(suffix, p):
        child = f"{name}_{suffix}"
        if child not in registry and len(registry) < MAX_CONTESTANTS:
            registry[child] = p; born.append(child)
    if params["fn"] == "event_drift":
        for dt in (-0.01, +0.01):
            t = round(params["threshold"] + dt, 3)
            if 0.02 <= t <= 0.08:
                add(f"t{int(t*1000)}", {**params, "threshold": t})
        for dh in (-1, +1):
            h = params["hold"] + dh
            if 2 <= h <= 5:
                add(f"h{h}", {**params, "hold": h})
    elif params["fn"] == "momentum":
        for dl in (-20, +20):
            lb = params["lookback"] + dl
            if 20 <= lb <= 120:
                add(f"lb{lb}", {**params, "lookback": lb})
    return born

# ---------------- state ----------------
def blank_stats():
    return dict(rung=0, days_on_rung=0, equity=1.0, peak=1.0, positions={},
                trades=0, days_in_market=0, sum_ret=0.0, sum_sq=0.0,
                paper_failures=0, retired=False, history=[])

def load_state():
    os.makedirs(STATE_DIR, exist_ok=True)
    p = os.path.join(STATE_DIR, "ledger.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {"registry": seed_registry(), "contestants": {}}

def save_state(s):
    json.dump(s, open(os.path.join(STATE_DIR, "ledger.json"), "w"), indent=1)

def fetch_prices():
    import yfinance as yf
    px = yf.download(ALL_TICKERS, period="1y", auto_adjust=True,
                     progress=False)["Close"]
    return px.dropna(how="all").ffill()

# ---------------- daily arena ----------------
def update():
    px = fetch_prices()
    today = str(px.index[-1].date())
    todays_ret = px.pct_change().iloc[-1]
    state = load_state()
    reg, con = state["registry"], state["contestants"]

    for name, params in reg.items():
        s = con.setdefault(name, blank_stats())
        if s["retired"]:
            continue
        # P&L from positions decided yesterday (no lookahead)
        day_ret = sum(w * todays_ret.get(t, 0.0)
                      for t, w in s["positions"].items())
        try:
            targets = IMPLS[params["fn"]](px, params)
        except Exception as e:
            targets = {}
            print(f"  [warn] {name}: {e}")
        tickers = set(s["positions"]) | set(targets)
        turn = sum(abs(targets.get(t, 0) - s["positions"].get(t, 0))
                   for t in tickers)
        net = day_ret - turn * COST_PER_SIDE
        s["equity"] *= (1 + net)
        s["peak"] = max(s["peak"], s["equity"])
        s["days_on_rung"] += 1
        s["trades"] += 1 if turn > 0.01 else 0
        if s["positions"]:
            s["days_in_market"] += 1
            s["sum_ret"] += net
            s["sum_sq"] += net * net
        s["positions"] = targets
        s["history"].append([today, round(net, 6), round(s["equity"], 5)])
        s["history"] = s["history"][-1300:]
    save_state(state)
    live = sum(1 for c in con.values() if not c["retired"])
    print(f"Arena updated {today}: {live} live contestants "
          f"({sum(1 for c in con.values() if c['retired'])} retired).")

# ---------------- weekly tournament ----------------
def report():
    state = load_state()
    reg, con = state["registry"], state["contestants"]
    R = RULES
    rows = []
    for name, s in con.items():
        if s["retired"]:
            continue
        n = max(s["days_in_market"], 1)
        mean = s["sum_ret"] / n
        var = max(s["sum_sq"] / n - mean ** 2, 1e-12)
        sharpe = mean / np.sqrt(var) * np.sqrt(252)
        dd = s["equity"] / s["peak"] - 1
        verdict = "hold"
        if dd < R["max_drawdown"]:
            verdict = "DEMOTE"
        elif (s["days_on_rung"] >= R["min_days_on_rung"]
              and s["trades"] >= R["min_trades"]
              and mean >= R["min_expectancy"]
              and sharpe >= R["min_sharpe"]):
            verdict = "PROMOTE"
        rows.append(dict(strategy=name, rung=s["rung"],
                         capital=f"Rs {LADDER[s['rung']]:,}",
                         days=s["days_on_rung"], trades=s["trades"],
                         equity=round(s["equity"], 3),
                         sharpe=round(sharpe, 2),
                         dd=f"{dd*100:.1f}%", verdict=verdict))
    df = pd.DataFrame(rows).sort_values(["rung", "sharpe"], ascending=False)
    print(df.to_string(index=False))

    # apply verdicts + evolution
    for r in rows:
        s = con[r["strategy"]]
        if r["verdict"] == "PROMOTE":
            s["rung"] = min(s["rung"] + 1, len(LADDER) - 1)
            s["days_on_rung"] = 0
            if s["rung"] >= 2:                       # proven with real money
                kids = spawn_children(r["strategy"], reg[r["strategy"]], reg)
                if kids:
                    print(f"  spawned children of {r['strategy']}: {kids}")
        elif r["verdict"] == "DEMOTE":
            if s["rung"] == 0:
                s["paper_failures"] += 1
                if s["paper_failures"] >= R["max_paper_failures"]:
                    s["retired"] = True
                    print(f"  retired: {r['strategy']}")
                else:                                 # fresh paper attempt
                    con[r["strategy"]] = {**blank_stats(),
                                          "paper_failures": s["paper_failures"]}
            else:
                s["rung"] -= 1
                s["days_on_rung"] = 0
                s["peak"] = s["equity"]
    save_state(state)
    print("\nRungs: 0=paper, then Rs 10k / 25k / 50k / 1L per strategy. "
          "Real-money rungs mean YOU place/fund those trades deliberately.")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "update"
    {"update": update, "report": report}[cmd]()