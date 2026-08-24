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
import json, sys, os, random
import numpy as np
import pandas as pd

STATE_DIR = "factory_state"
COST_PER_SIDE = 0.0019            # legacy flat-rate constant, kept for reference/
                                   # display only -- update() no longer charges
                                   # against this directly, see round_trip_cost().
                                   # See EXECUTION_PLAN.md P0-1: a flat percentage
                                   # understates real Indian equity delivery costs
                                   # by up to ~3x at the position sizes LADDER
                                   # rung 1 actually implies, because real costs
                                   # have a FIXED component (the DP charge) that
                                   # a flat rate can't represent.
VARIABLE_COST_PER_SIDE = 0.00111  # STT+exchange txn+stamp+GST, ~0.222% round
                                   # trip / 2, charged per side on traded notional
DP_CHARGE_PER_SCRIP = 15.34       # Rs, FIXED, once per scrip per sell-day --
                                   # this is the fixed component a flat-percentage
                                   # model misses entirely
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
MIN_SHARPE_SAMPLE_DAYS = 20   # below this, the variance estimate behind Sharpe
                               # is unreliable (a few near-identical returns can
                               # floor variance near zero and blow Sharpe up to
                               # an absurd value) -- same guard advisors.py's own
                               # sharpe() uses. This does not loosen or tighten
                               # RULES["min_sharpe"]; it only stops an
                               # under-sampled Sharpe from ever satisfying it.

# ---------------- advisor layer (see advisors.py) -----------------------
# Historical-parameter advisors may only ever propose a mutated REPLACEMENT
# registry key for a paper-tier (rung 0) contestant -- never edit an
# existing entry in place, and never touch anything already on a
# real-money rung. Those still only evolve via spawn_children() above.
PARAM_BANK_PATH = os.path.join(STATE_DIR, "parameter_bank.json")
ADVISOR_STATE_PATH = os.path.join(STATE_DIR, "advisor_state.json")
EVOLUTION_TOP_N = 10          # only contestants ranked outside the overall
                               # top N are candidates for advisor-informed evolution
PARAM_BOUNDS = {               # mechanism-bounded blend ranges, mirrors seed grid
    "threshold": (0.02, 0.08, 3), "hold": (2, 5, 0),
    "lookback": (20, 120, 0), "lb": (10, 40, 0), "drop": (-0.08, -0.03, 3),
}

# ---------------- paper P&L display + breeding (paper tier only) --------
# PAPER_STARTING_CAPITAL is a DISPLAY convenience, not a financial risk
# parameter -- it does not change any trading math, promotion threshold,
# or real capital. paper_capital = equity * PAPER_STARTING_CAPITAL just
# turns the existing equity multiplier into a human-readable rupee P&L for
# rung-0 (paper, Rs 0 real risk) contestants. Real-money rungs still use
# LADDER for actual capital.
PAPER_STARTING_CAPITAL = 100_000

# Reproduction, not replacement: a profitable top-BREEDING_TOP_N paper-tier
# contestant can mate with another (same family + sector -- a real
# mechanism constraint, see crossover_breed()) and produce an ADDITIONAL
# child without losing its own slot. Distinct from propose_evolutions()'s
# bottom-of-tournament replacement mechanism. Paper tier only -- real-money
# rungs never breed this way, only via the pre-existing spawn_children()
# on promotion.
BREEDING_TOP_N = 10
BREEDING_MIN_TRADES = RULES["min_trades"]   # need real evidence, not luck
BREEDING_MAX_NEW_PER_ROUND = 3              # caps a single report() round's births

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
    elif params["fn"] == "input_cost":
        # Same mechanism-bounded neighbour-variant approach as the other
        # families above (ranges match PARAM_BOUNDS), just never written
        # for this family until now -- input_cost/monsoon breeding was an
        # open question in 03_learnings_and_suggestions.txt. monsoon is
        # deliberately still excluded: it's a dormant no-op with no CSV
        # sourced yet (sig_monsoon), so breeding it would produce children
        # that can never generate a signal either -- revisit once the CSV
        # exists.
        for dlb in (-5, +5):
            lb = params["lb"] + dlb
            if 10 <= lb <= 40:
                add(f"lb{lb}", {**params, "lb": lb})
        for dd in (-0.01, +0.01):
            drop = round(params["drop"] + dd, 3)
            if -0.08 <= drop <= -0.03:
                add(f"d{int(abs(drop)*1000)}", {**params, "drop": drop})
    return born

# ---------------- state ----------------
def blank_stats(lineage=None):
    return dict(rung=0, days_on_rung=0, equity=1.0, peak=1.0, positions={},
                trades=0, days_in_market=0, sum_ret=0.0, sum_sq=0.0,
                paper_failures=0, retired=False, history=[],
                lineage=lineage, evolved_out=False, trust_scored=False)

def load_state():
    os.makedirs(STATE_DIR, exist_ok=True)
    p = os.path.join(STATE_DIR, "ledger.json")
    if not os.path.exists(p):
        return {"registry": seed_registry(), "contestants": {}}
    state = json.load(open(p))
    for s in state["contestants"].values():   # backfill pre-advisor-layer entries
        s.setdefault("lineage", None)
        s.setdefault("evolved_out", False)
        s.setdefault("trust_scored", False)
    return state

def save_state(s):
    json.dump(s, open(os.path.join(STATE_DIR, "ledger.json"), "w"), indent=1)

def load_json(path, default):
    return json.load(open(path)) if os.path.exists(path) else default

def save_json(path, obj):
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1)

def load_parameter_bank():
    return load_json(PARAM_BANK_PATH, {"bank": {}})

def load_advisor_state():
    return load_json(ADVISOR_STATE_PATH,
                      {"trust_weight": 0.25, "history": []})

def fetch_prices():
    import yfinance as yf
    px = yf.download(ALL_TICKERS, period="1y", auto_adjust=True,
                     progress=False)["Close"]
    return px.dropna(how="all").ffill()

def round_trip_cost(turn, tickers_sold, effective_capital):
    """Size-aware transaction cost for one day's rebalance, as a fraction
    of NAV. EXECUTION_PLAN.md P0-1: real Indian equity delivery cost is
    ~0.222% of position (variable: STT+exchange txn+stamp+GST) PLUS a
    FIXED Rs 15.34 DP charge per scrip per sell-day. A flat percentage
    (the old COST_PER_SIDE) can only be right at one position size and
    is wrong -- too low -- everywhere below it, which is exactly the
    size range LADDER's early rungs imply.

    turn: existing turnover measure, sum of abs(weight change) across
      all tickers (both the sell leg and buy leg of a full rebalance
      each contribute, so turn=2.0 for a full close-and-reopen).
    tickers_sold: count of tickers whose weight DECREASED today (a
      full close or a partial trim) -- each triggers one DP charge
      regardless of position size, which is precisely where a flat
      percentage model breaks down at small sizes.
    effective_capital: rupees the contestant's weight=1.0 represents.
      For a real-money rung (>=1) this is that rung's own LADDER
      capital. For paper tier (rung 0, LADDER=Rs 0 -- costing against
      that would divide by zero and is meaningless anyway) this is
      LADDER[1]: paper contestants are costed as if already funded at
      the first real rung, because that's the capital level whose
      economics actually determines whether promoting them makes
      sense. This does not change LADDER itself, only which rung's
      capital a paper contestant's cost is benchmarked against.
    """
    variable = turn * VARIABLE_COST_PER_SIDE
    fixed = (tickers_sold * DP_CHARGE_PER_SCRIP / effective_capital
             if effective_capital > 0 else 0.0)
    return variable + fixed

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
        tickers_sold = sum(1 for t in tickers
                            if targets.get(t, 0) < s["positions"].get(t, 0) - 1e-9)
        effective_capital = LADDER[max(s["rung"], 1)]
        net = day_ret - round_trip_cost(turn, tickers_sold, effective_capital)
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

# ---------------- advisor-informed evolution (paper tier only) ----------
def mutate_params(current, advisor_params, weight):
    """Blend a contestant's current numeric hyperparameters toward the
    advisor bank's top pick for its (family, sector) bucket, weighted by
    the tournament's current trust_weight. Categorical fields (fn, sector,
    leader, proxy) are never changed -- only numeric params inside the
    same mechanism-bounded range the seed grid already uses."""
    out = dict(current)
    for key, (lo, hi, decimals) in PARAM_BOUNDS.items():
        if key in current and key in advisor_params:
            blended = (1 - weight) * current[key] + weight * advisor_params[key]
            blended = min(max(blended, lo), hi)
            out[key] = round(blended, decimals) if decimals else int(round(blended))
    return out

def propose_evolutions(rows, reg, con, bank, trust_weight):
    """Rank all live contestants tournament-wide (same order as the report
    table); any rung-0 contestant outside the top EVOLUTION_TOP_N, with
    enough evaluation history, gets retired in favor of ONE new registry
    key mutated toward the advisor bank's best pick. Never mutates an
    entry in place (Law 2's mechanical invariant) and never touches a
    contestant already on a real-money rung."""
    born = []
    for rank, r in enumerate(rows, start=1):
        if rank <= EVOLUTION_TOP_N:
            continue
        name = r["strategy"]
        s = con[name]
        if (s["rung"] != 0 or s["retired"] or s["evolved_out"]
                or s["days_on_rung"] < RULES["min_days_on_rung"]
                or s["trades"] < RULES["min_trades"]):
            continue
        params = reg[name]
        fn, sector = params["fn"], params.get("sector")
        picks = bank.get(fn, {}).get(sector)
        if not picks:
            continue
        best = picks[0]["params"]
        new_params = mutate_params(params, best, trust_weight)
        if new_params == params:
            continue
        gen = (s["lineage"] or {}).get("gen", 0) + 1 if s["lineage"] else 1
        if len(reg) >= MAX_CONTESTANTS:
            continue
        child = f"{name}_evo{gen}"
        suffix = 2
        while child in reg:
            child = f"{name}_evo{gen}_{suffix}"; suffix += 1
        mean = s["sum_ret"] / max(s["days_in_market"], 1)
        reg[child] = new_params
        con[child] = blank_stats(lineage=dict(
            parents=[name], mechanism="advisor_evolve", gen=gen,
            advisor_weight_used=trust_weight,
            parent_mean_ret=round(mean, 6), parent_rank=rank,
            bank_source=picks[0]))
        s["retired"] = True
        s["evolved_out"] = True
        born.append(child)
    return born

def crossover_breed(parent_a, parent_b):
    """Combine two same-family, same-sector parents' calibrated numeric
    parameters into a child's. Uniform per-gene inheritance -- each
    numeric parameter independently inherited from a or b with equal
    probability, mirroring biological crossover rather than just
    averaging. Categorical fields (fn, sector, leader/proxy) must already
    match between parents (enforced by the caller) and carry over as-is.

    Mechanism (Law 1 requires one): when two independently-conceived
    hypotheses in the same family and sector have both proven profitable
    in live paper trading, recombining their calibrated parameters is a
    reasonable bet the child inherits calibration quality from both --
    the trading-strategy equivalent of ensembling two independently
    validated parameter fits. This is not data-mining a new mechanism;
    both inputs already cleared the same live-evidence bar as everything
    else in the tournament.

    Never mutates either parent -- returns a fresh params dict only."""
    assert parent_a["fn"] == parent_b["fn"]
    assert parent_a.get("sector") == parent_b.get("sector")
    child = dict(parent_a)
    gene_map = {}
    for key in PARAM_BOUNDS:
        if key in parent_a and key in parent_b:
            source = random.choice(("a", "b"))
            child[key] = parent_a[key] if source == "a" else parent_b[key]
            gene_map[key] = source
    return child, gene_map

def attempt_breeding(reg, con):
    """Top-BREEDING_TOP_N profitable paper-tier contestants may mate and
    produce an additional child -- 'they need to earn to reproduce'.
    Ranked among paper-tier (rung 0) contestants only, by equity; a
    real-money-rung contestant is never part of this ranking or pool.
    Eligibility: profitable (equity > 1.0) with real evidence (enough
    trades), not already retired/evolved-out this round. Within each
    (family, sector) bucket the two fittest eligible parents mate --
    crossover requires a shared mechanism, see crossover_breed(). Bounded
    by MAX_CONTESTANTS and BREEDING_MAX_NEW_PER_ROUND so a lucky week
    can't explode the population."""
    paper_live = [(n, s) for n, s in con.items()
                  if s["rung"] == 0 and not s["retired"] and not s["evolved_out"]]
    paper_live.sort(key=lambda ns: ns[1]["equity"], reverse=True)
    eligible = [n for n, s in paper_live[:BREEDING_TOP_N]
                if s["equity"] > 1.0 and s["trades"] >= BREEDING_MIN_TRADES]

    buckets = {}
    for name in eligible:
        p = reg[name]
        buckets.setdefault((p["fn"], p.get("sector")), []).append(name)
    bucket_keys = list(buckets.keys())
    random.shuffle(bucket_keys)

    born = []
    for key in bucket_keys:
        if len(born) >= BREEDING_MAX_NEW_PER_ROUND or len(reg) >= MAX_CONTESTANTS:
            break
        members = buckets[key]
        if len(members) < 2:
            continue
        members.sort(key=lambda n: con[n]["equity"], reverse=True)
        a, b = members[0], members[1]        # the two fittest in this bucket mate
        child_params, gene_map = crossover_breed(reg[a], reg[b])
        gen = max((con[a]["lineage"] or {}).get("gen", 0),
                  (con[b]["lineage"] or {}).get("gen", 0)) + 1
        # Truncate parent names in the child's name -- without this, names
        # concatenate across generations and grow unbounded (seen in
        # testing: chains like "x_x_x_..." after several breeding rounds).
        # Full ancestry is still preserved exactly in lineage["parents"].
        short_a, short_b = a[:18], b[:18]
        child = f"{short_a}_x_{short_b}_g{gen}"
        base, suffix = child, 2
        while child in reg:
            child = f"{base}_{suffix}"; suffix += 1
        reg[child] = child_params
        con[child] = blank_stats(lineage=dict(
            parents=[a, b], mechanism="crossover", gen=gen, gene_map=gene_map))
        born.append(child)
    return born

def update_advisor_trust(con, adv_state):
    """'How much to listen to the advisor' is decided collectively: every
    advisor-evolved lineage child that has finished its own evaluation
    window is scored against the parent it replaced. If most of them beat
    their parent's mean return, nudge trust_weight up; otherwise nudge it
    down. Only scores mechanism="advisor_evolve" lineage -- crossover and
    spawn_neighbor children don't have a single "parent replaced" to
    compare against, so they're not part of this vote."""
    beat, total = 0, 0
    for s in con.values():
        if (not s["lineage"] or s["lineage"].get("mechanism") != "advisor_evolve"
                or s["trust_scored"]
                or s["days_on_rung"] < RULES["min_days_on_rung"]):
            continue
        child_mean = s["sum_ret"] / max(s["days_in_market"], 1)
        total += 1
        if child_mean > s["lineage"]["parent_mean_ret"]:
            beat += 1
        s["trust_scored"] = True
    if total == 0:
        return adv_state
    step = 0.05 if beat * 2 > total else -0.05
    new_weight = min(max(adv_state["trust_weight"] + step, 0.05), 0.9)
    adv_state["trust_weight"] = round(new_weight, 3)
    adv_state["history"].append(dict(
        date=str(pd.Timestamp.now(tz="UTC").date()),
        children_evaluated=total, children_beat_parent=beat,
        new_trust_weight=adv_state["trust_weight"]))
    adv_state["history"] = adv_state["history"][-100:]
    return adv_state

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
        if s["days_in_market"] < MIN_SHARPE_SAMPLE_DAYS:
            sharpe = float("nan")   # not enough data for a reliable estimate
        else:
            var = max(s["sum_sq"] / n - mean ** 2, 1e-12)
            sharpe = mean / np.sqrt(var) * np.sqrt(252)
        dd = s["equity"] / s["peak"] - 1
        verdict = "hold"
        if dd < R["max_drawdown"]:
            verdict = "DEMOTE"
        elif (s["days_on_rung"] >= R["min_days_on_rung"]
              and s["trades"] >= R["min_trades"]
              and mean >= R["min_expectancy"]
              and sharpe >= R["min_sharpe"]):   # NaN >= anything is False
            verdict = "PROMOTE"
        paper_pnl = s["equity"] * PAPER_STARTING_CAPITAL - PAPER_STARTING_CAPITAL
        rows.append(dict(strategy=name, rung=s["rung"],
                         capital=f"Rs {LADDER[s['rung']]:,}",
                         days=s["days_on_rung"], trades=s["trades"],
                         equity=round(s["equity"], 3),
                         sharpe=round(sharpe, 2),
                         dd=f"{dd*100:.1f}%", verdict=verdict,
                         paper_pnl=f"Rs {paper_pnl:+,.0f}"))
    df = pd.DataFrame(rows).sort_values(["rung", "sharpe"], ascending=False)
    print(df.to_string(index=False))
    ranked_rows = df.to_dict("records")   # tournament-wide rank order (1 = best)

    # apply verdicts + evolution
    for r in rows:
        s = con[r["strategy"]]
        if r["verdict"] == "PROMOTE":
            s["rung"] = min(s["rung"] + 1, len(LADDER) - 1)
            s["days_on_rung"] = 0
            if s["rung"] >= 2:                       # proven with real money
                kids = spawn_children(r["strategy"], reg[r["strategy"]], reg)
                if kids:
                    parent_gen = (s["lineage"] or {}).get("gen", 0)
                    for k in kids:
                        con[k] = blank_stats(lineage=dict(
                            parents=[r["strategy"]], mechanism="spawn_neighbor",
                            gen=parent_gen + 1))
                    print(f"  spawned children of {r['strategy']}: {kids}")
        elif r["verdict"] == "DEMOTE":
            if s["rung"] == 0:
                s["paper_failures"] += 1
                if s["paper_failures"] >= R["max_paper_failures"]:
                    s["retired"] = True
                    print(f"  retired: {r['strategy']}")
                else:                                 # fresh paper attempt
                    con[r["strategy"]] = {**blank_stats(lineage=s["lineage"]),
                                          "paper_failures": s["paper_failures"]}
            else:
                s["rung"] -= 1
                s["days_on_rung"] = 0
                s["peak"] = s["equity"]

    # advisor layer: evolve paper-tier stragglers, then re-score trust
    bank = load_parameter_bank().get("bank", {})
    adv_state = load_advisor_state()
    evolved = propose_evolutions(ranked_rows, reg, con, bank,
                                  adv_state["trust_weight"])
    if evolved:
        print(f"  advisor-evolved (rank > {EVOLUTION_TOP_N}, paper tier): "
              f"{evolved}  [trust_weight={adv_state['trust_weight']}]")
    adv_state = update_advisor_trust(con, adv_state)
    save_json(ADVISOR_STATE_PATH, adv_state)

    # breeding: profitable top-BREEDING_TOP_N paper-tier contestants mate
    born = attempt_breeding(reg, con)
    if born:
        print(f"  bred (top {BREEDING_TOP_N} profitable, paper tier): {born}")

    save_state(state)
    print("\nRungs: 0=paper, then Rs 10k / 25k / 50k / 1L per strategy. "
          "Real-money rungs mean YOU place/fund those trades deliberately.")

    # additive-only advisory layers -- read the already-saved state, never
    # write ledger.json, never influence a verdict above. See agents/README.md.
    try:
        from agents.risk_manager.risk_manager import report as risk_report
        from agents.reporter.reporter import weekly_digest
        risk_report(state)
        weekly_digest(rows, evolved, born, state)
    except Exception as e:
        print(f"  [warn] agents/ advisory layer failed (non-fatal, does not "
              f"affect verdicts above): {e}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "update"
    {"update": update, "report": report}[cmd]()