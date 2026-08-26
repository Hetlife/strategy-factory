import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time
import os
import sys
from datetime import datetime, timezone

# --- CONFIGURATION ---
GITHUB_USER = "Hetlife"
REPO_NAME = "strategy-factory"
BRANCH = "main"
FILE_PATH = "factory_state/ledger.json"
ADVISOR_STATE_PATH = "factory_state/advisor_state.json"
PARAM_BANK_PATH = "factory_state/parameter_bank.json"
STATE_JSON_PATH = ".autonomous/state.json"
PAPER_STARTING_CAPITAL = 100_000   # must match factory.py's constant -- display only
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           ".autonomous", "dashboard_notes.md")

# agents/ modules are pure functions over a ledger_state dict (no local
# ledger.json needed -- the live-fetched `data` dict from GitHub IS that
# dict, same shape load_state() returns). Only works when this file is run
# from inside a full local clone of the repo, since it imports factory.py
# and agents/ as local modules -- exactly the "run it locally" setup.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import numpy as _np
    import factory as _factory
    from agents.judge.judge import explain_verdict, who_is_eligible_for_promotion
    from agents.breeder.breeder import lineage_tree
    from agents.risk_manager.risk_manager import (
        sector_concentration, aggregate_real_money_exposure,
        portfolio_drawdown_correlation_flag,
    )
    AGENTS_AVAILABLE = True
except Exception as _agents_import_error:
    AGENTS_AVAILABLE = False


def _live_sharpe_and_tax(s):
    """Recomputes report()'s exact Sharpe/post-tax-expectancy formulas from
    a contestant's own stored stats -- same numbers report() would print,
    just derived here for the dashboard's live re-ranking toggle instead of
    needing a full report() run. Read-only, no state mutation."""
    n = max(s.get("days_in_market", 0), 1)
    mean = s.get("sum_ret", 0.0) / n
    if s.get("days_in_market", 0) < _factory.MIN_SHARPE_SAMPLE_DAYS:
        sharpe = float("nan")
    else:
        var = max(s.get("sum_sq", 0.0) / n - mean ** 2, 1e-12)
        sharpe = mean / _np.sqrt(var) * _np.sqrt(252)
    pt_mean, _ = _factory.post_tax_expectancy(mean, s.get("days_in_market", 0),
                                               s.get("trades", 0))
    return sharpe, pt_mean

st.set_page_config(page_title="Strategy Factory Arena", layout="wide", page_icon="🤖")

# --- SIDEBAR & REFRESH BUTTON ---
st.sidebar.title("🔄 Controls")

if st.sidebar.button("Refresh Data Now"):
    st.cache_data.clear()
    st.toast("Fetching latest data from GitHub...", icon="⏳")
    time.sleep(1)
    st.rerun()

# --- CACHED DATA LOADERS ---
def _fetch_json(path, ts):
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/refs/heads/{BRANCH}/{path}?t={ts}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

@st.cache_data(ttl=60)
def load_ledger_data(ts):
    data = _fetch_json(FILE_PATH, ts)
    if data is None:
        st.error("Failed to fetch ledger data from GitHub.")
    return data

@st.cache_data(ttl=60)
def load_advisor_state(ts):
    # Optional: absent until the first monthly advisor-training run lands.
    return _fetch_json(ADVISOR_STATE_PATH, ts)

@st.cache_data(ttl=60)
def load_parameter_bank(ts):
    return _fetch_json(PARAM_BANK_PATH, ts)

@st.cache_data(ttl=60)
def load_state_json(ts):
    return _fetch_json(STATE_JSON_PATH, ts)

# --- LOAD DATA ---
current_timestamp = int(time.time())
data = load_ledger_data(current_timestamp)
advisor_state = load_advisor_state(current_timestamp)
parameter_bank = load_parameter_bank(current_timestamp)
state_json = load_state_json(current_timestamp)

tab_arena, tab_office = st.tabs(["📊 Arena", "🏢 The Office"])

# ============================================================ ARENA TAB ===
with tab_arena:
    if data and "contestants" in data:
        st.title("🤖 Strategy Factory Trading Arena")
        st.markdown("Tracking algorithmic strategy performance and investment growth in real-time.")

        contestants = data["contestants"]

        total_strategies = len(contestants)
        active_strategies = sum(1 for c in contestants.values() if not c.get("retired", False))

        all_series = {}
        metric_cards_data = []

        for name, config in contestants.items():
            history = config.get("history", [])
            if history:
                df = pd.DataFrame(history, columns=["Date", "Return", "Equity"])
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date")
                all_series[name] = df

                lineage = config.get("lineage")
                equity = config.get("equity", 1.0)
                paper_pnl = equity * PAPER_STARTING_CAPITAL - PAPER_STARTING_CAPITAL

                if lineage:
                    parents = lineage.get("parents") or [lineage.get("parent")]
                    mechanism = lineage.get("mechanism", "advisor_evolve")
                    gen = lineage.get("gen", "?")
                    icon = {"crossover": "🧬💞", "spawn_neighbor": "🌱",
                            "advisor_evolve": "🧬"}.get(mechanism, "🧬")
                    verb = {"crossover": "bred from", "spawn_neighbor": "spawned from",
                            "advisor_evolve": "evolved from"}.get(mechanism, "from")
                    lineage_str = f"{icon} {verb} {' × '.join(parents)} (gen {gen})"
                else:
                    lineage_str = "seed"

                row = {
                    "Strategy": name,
                    "Current Equity": equity,
                    "Peak Equity": config.get("peak", 1.0),
                    "Paper P&L (Rs)": round(paper_pnl),
                    "Trades Executed": config.get("trades", 0),
                    "Days in Market": config.get("days_in_market", 0),
                    "Status": ("Evolved out" if config.get("evolved_out")
                               else "Retired" if config.get("retired", False)
                               else "Active"),
                    "Lineage": lineage_str,
                }
                if AGENTS_AVAILABLE:
                    sharpe, pt_mean = _live_sharpe_and_tax(config)
                    row["Sharpe"] = round(sharpe, 3) if sharpe == sharpe else None  # NaN check
                    row["Post-tax Expectancy"] = round(pt_mean, 6)
                metric_cards_data.append(row)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Contestants", total_strategies)
        col2.metric("Active Strategies", active_strategies)
        col3.metric("Paper Bankroll / Contestant", f"Rs {PAPER_STARTING_CAPITAL:,}",
                    help="Every contestant starts here on paper (rung 0 = Rs 0 real "
                         "money at risk). Paper P&L below is this times the equity "
                         "factor -- a bookkeeping display, not a real balance.")

        if metric_cards_data:
            avg_equity = pd.DataFrame(metric_cards_data)["Current Equity"].mean()
            col4.metric("Average Arena Equity Factor", f"{avg_equity:.2f}x")

        st.markdown("---")
        st.subheader("📈 Arena Equity Growth Comparison")

        fig = go.Figure()
        for name, df in all_series.items():
            fig.add_trace(go.Scatter(
                x=df["Date"],
                y=df["Equity"],
                mode='lines+markers',
                name=name
            ))

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Equity Value (Normalized to 1.0)",
            hovermode="x unified",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("🏆 Strategy Leaderboard")
        if metric_cards_data:
            summary_df = pd.DataFrame(metric_cards_data)
            rank_options = ["Current Equity", "Paper P&L (Rs)"]
            if "Sharpe" in summary_df.columns:
                rank_options += ["Sharpe", "Post-tax Expectancy"]
            rank_by = st.selectbox(
                "Rank leaderboard by:", rank_options, index=0,
                help="Re-sorts the table below live -- doesn't change any "
                     "actual promotion/demotion verdict, which always uses "
                     "report()'s own pre-tax Sharpe per RULES."
            )
            sorted_df = summary_df.sort_values(
                by=rank_by, ascending=False, na_position="last")
            st.dataframe(
                sorted_df,
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")
        st.subheader("🧭 Advisor Layer")
        st.caption(
            "Historical-parameter advisors trained monthly on price data (advisors.py). "
            "They only ever propose a mutated REPLACEMENT for a paper-tier (rung 0) "
            "contestant ranked outside the tournament's top 10 — never a real-money "
            "rung, and never an edit in place."
        )

        if advisor_state:
            trust = advisor_state.get("trust_weight", 0.0)
            adv_col1, adv_col2 = st.columns([1, 2])
            adv_col1.metric("Advisor Trust Weight", f"{trust:.2f}",
                             help="How much the tournament currently blends advisor-"
                                  "recommended parameters into evolved contestants "
                                  "(0 = ignore advisor, 1 = fully adopt its pick). "
                                  "Self-tunes each week based on whether prior "
                                  "advisor-evolved children beat the parent they replaced.")
            history = advisor_state.get("history", [])
            if history:
                hist_df = pd.DataFrame(history)
                trust_fig = go.Figure()
                trust_fig.add_trace(go.Scatter(
                    x=hist_df["date"], y=hist_df["new_trust_weight"],
                    mode="lines+markers", name="trust_weight"))
                trust_fig.update_layout(
                    template="plotly_dark", height=260,
                    yaxis_title="trust_weight", xaxis_title="Date")
                adv_col2.plotly_chart(trust_fig, use_container_width=True)
            else:
                adv_col2.info("No lineage children have finished their evaluation "
                               "window yet — trust weight hasn't been re-scored.")
        else:
            st.info("No advisor_state.json yet — trust weight starts at its default "
                    "(0.25) until the first evolution round runs.")

        if parameter_bank and parameter_bank.get("bank"):
            st.markdown("**Parameter bank — top advisor picks per strategy family / sector**")
            st.caption(f"Last trained: {parameter_bank.get('generated_at', 'unknown')} "
                       f"· advisors: {', '.join(parameter_bank.get('advisors', []))}")
            skip_keys = {"fn", "sector"}
            bank_rows = []
            for fn, sectors in parameter_bank["bank"].items():
                for sector, picks in sectors.items():
                    for rank, pick in enumerate(picks, start=1):
                        readable = ", ".join(
                            f"{k}={v}" for k, v in pick["params"].items()
                            if k not in skip_keys)
                        bank_rows.append({
                            "Family": fn, "Sector": sector, "Rank": rank,
                            "Params": readable, "Sharpe": pick["sharpe"],
                            "Robustness": pick["robustness"],
                            "Cost Efficiency (bps/round-trip)": pick["cost_efficiency"],
                        })
            st.dataframe(pd.DataFrame(bank_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No parameter_bank.json yet — waiting for the first monthly "
                    "advisor-training run (advisor_training.yml).")
    else:
        st.warning("Waiting for data stream structure. Make sure your repository has executed a successful update.")

# ============================================================ OFFICE TAB ==
with tab_office:
    st.title("🏢 The Office")
    st.markdown(
        "Each strategy-factory agent has one job. This view shows what each "
        "one is actually looking at right now, computed live from the same "
        "ledger the Arena tab shows above — not a separate simulation."
    )

    if not AGENTS_AVAILABLE:
        st.error(
            "Couldn't import agents/ or factory.py locally — this tab only "
            "works when dashboard.py is run from inside a full clone of the "
            "repo (`git clone` then `streamlit run dashboard.py`), not a "
            "standalone copy of this one file. Import error: "
            f"`{_agents_import_error}`"
        )
    elif not data or "contestants" not in data:
        st.warning("Waiting on ledger data — see the Arena tab.")
    else:
        desk1, desk2, desk3 = st.columns(3)
        desk4, desk5, desk6 = st.columns(3)

        # --- Judge ---
        with desk1:
            st.markdown("### ⚖️ Judge")
            st.caption("Decides who's ready to move up — re-derives the exact "
                       "same math report() uses, read-only.")
            eligible = who_is_eligible_for_promotion(data)
            if eligible:
                st.success(f"{len(eligible)} contestant(s) currently meet every "
                           f"PROMOTE threshold:")
                for name in eligible:
                    st.write(f"— {name}")
            else:
                st.info("Nobody clears every promotion threshold right now — "
                        "normal in Phase 0/1, not a problem.")
            live_names = [n for n, c in data["contestants"].items() if not c.get("retired")]
            if live_names:
                pick = max(live_names, key=lambda n: data["contestants"][n].get("equity", 1.0))
                with st.expander(f"Why does '{pick}' (best performer) have its current verdict?"):
                    st.code(explain_verdict(pick, data), language=None)

        # --- Researcher ---
        with desk2:
            st.markdown("### 🔬 Researcher")
            st.caption("Backtests parameter grids monthly on historical data, "
                       "ranks candidates for the advisor-evolution mechanism.")
            if parameter_bank and parameter_bank.get("bank"):
                n_buckets = sum(len(v) for v in parameter_bank["bank"].values())
                st.success(f"Trained: {n_buckets} (family, sector) buckets ranked.")
                st.caption(f"Last run: {parameter_bank.get('generated_at', 'unknown')}")
                st.caption("Full picks table is in the Arena tab below the "
                          "Advisor Layer chart.")
            else:
                st.info("Hasn't run yet — first monthly training "
                        "(advisor_training.yml) is still pending.")

        # --- Breeder ---
        with desk3:
            st.markdown("### 🧬 Breeder")
            st.caption("Renders the family tree factory.py already records — "
                       "never creates a contestant itself.")
            tree = lineage_tree(data)
            if tree:
                st.success(f"{len(tree)} contestant(s) with recorded lineage:")
                for name, desc in list(tree.items())[:8]:
                    st.write(f"**{name}** — {desc}")
                if len(tree) > 8:
                    st.caption(f"... and {len(tree) - 8} more.")
            else:
                st.info("No bred/evolved children yet — every live contestant "
                        "is still an original seed.")

        # --- Risk Manager ---
        with desk4:
            st.markdown("### 🛡️ Risk Manager")
            st.caption("Second set of eyes on portfolio-level risk no single "
                       "contestant's verdict can see.")
            exposure = aggregate_real_money_exposure(data)
            if exposure == 0:
                st.success("Real-money exposure: Rs 0 (expected through Phase 0/1).")
            else:
                st.error(f"Real-money exposure: Rs {exposure:,} — verify this "
                         f"was a fresh, explicit authorization, not silent drift.")
            flagged, below, live_n = portfolio_drawdown_correlation_flag(data)
            if flagged:
                st.warning(f"{below}/{live_n} live contestants are in elevated "
                          f"drawdown together — possible correlated regime move.")
            else:
                st.caption(f"Drawdown correlation: {below}/{live_n} live "
                          f"contestants in elevated drawdown — not flagged.")
            conc = sector_concentration(data)
            if conc:
                with st.expander("Sector concentration"):
                    for sec, v in sorted(conc.items()):
                        st.write(f"**{sec}**: {v['contestants']} live"
                                + (f", Rs {v['capital']:,}" if v["capital"] else ""))

        # --- Reporter ---
        with desk5:
            st.markdown("### 📝 Reporter")
            st.caption("Translates report() output into plain English for "
                       "the weekly digest.")
            st.info(
                "Its live output only exists mid-`report()` run (it needs "
                "the same-round rows/evolved/born values), so it can't be "
                "replayed here without re-running the full weekly cycle. "
                "See the actual weekly digest in the GitHub Actions logs "
                "for `factory.yml`'s Sunday run, or run "
                "`python3 factory.py report` locally."
            )

        # --- Healer ---
        with desk6:
            st.markdown("### 🩹 Healer")
            st.caption("Scans repo consistency between operations — "
                       "detects only, never fixes anything itself.")
            if state_json:
                import json as _json
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    ledger_tmp = os.path.join(tmpdir, "ledger.json")
                    state_tmp = os.path.join(tmpdir, "state.json")
                    _json.dump(data, open(ledger_tmp, "w"))
                    _json.dump(state_json, open(state_tmp, "w"))
                    try:
                        from tools import health_check
                        findings = health_check.run_all(ledger_tmp, state_tmp)
                    except Exception as e:
                        findings = None
                        st.caption(f"(couldn't run tools/health_check.py: {e})")
                if findings is not None:
                    real = [f for f in findings if f[0] != "info"]
                    if real:
                        for level, msg in real:
                            (st.error if level == "error" else st.warning)(msg)
                    else:
                        st.success("No findings — repo trackers and ledger "
                                  "are internally consistent.")
            else:
                st.caption("state.json not fetched — can't run the full check "
                          "here, only the registry-vs-ledger part would apply.")

    st.markdown("---")
    st.subheader("📋 Notes")
    st.caption(
        "Not a live AI chat — this just saves what you type to a local file "
        "(`.autonomous/dashboard_notes.md`) so you can bring it to your next "
        "session with Claude. Only works when running locally (writes to "
        "disk); has no effect on a hosted/shared copy of this page."
    )
    note_text = st.text_area("Write a note or question to bring back later:", height=100)
    if st.button("Save note"):
        if note_text.strip():
            try:
                os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                with open(NOTES_FILE, "a") as f:
                    f.write(f"\n- **{timestamp}** — {note_text.strip()}\n")
                st.success(f"Saved to {NOTES_FILE}")
            except Exception as e:
                st.error(f"Couldn't save (read-only filesystem or hosted copy?): {e}")
        else:
            st.warning("Nothing to save — write something first.")

    if os.path.exists(NOTES_FILE):
        with st.expander("Previously saved notes"):
            st.markdown(open(NOTES_FILE).read())
