import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

# --- CONFIGURATION ---
GITHUB_USER = "Hetlife"
REPO_NAME = "strategy-factory"
BRANCH = "main"
FILE_PATH = "factory_state/ledger.json"
ADVISOR_STATE_PATH = "factory_state/advisor_state.json"
PARAM_BANK_PATH = "factory_state/parameter_bank.json"

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

# --- LOAD DATA ---
current_timestamp = int(time.time())
data = load_ledger_data(current_timestamp)
advisor_state = load_advisor_state(current_timestamp)
parameter_bank = load_parameter_bank(current_timestamp)

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
            metric_cards_data.append({
                "Strategy": name,
                "Current Equity": config.get("equity", 1.0),
                "Peak Equity": config.get("peak", 1.0),
                "Trades Executed": config.get("trades", 0),
                "Days in Market": config.get("days_in_market", 0),
                "Status": ("Evolved out" if config.get("evolved_out")
                           else "Retired" if config.get("retired", False)
                           else "Active"),
                "Lineage": (f"🧬 advisor-evolved from {lineage['parent']} "
                            f"(gen {lineage['gen']})" if lineage else "seed"),
            })

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Contestants", total_strategies)
    col2.metric("Active Strategies", active_strategies)
    
    if metric_cards_data:
        avg_equity = pd.DataFrame(metric_cards_data)["Current Equity"].mean()
        col3.metric("Average Arena Equity Factor", f"{avg_equity:.2f}x")

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
        st.dataframe(
            summary_df.sort_values(by="Current Equity", ascending=False),
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
        bank_rows = []
        for fn, sectors in parameter_bank["bank"].items():
            for sector, picks in sectors.items():
                for rank, pick in enumerate(picks, start=1):
                    bank_rows.append({
                        "Family": fn, "Sector": sector, "Rank": rank,
                        "Params": pick["params"], "Sharpe": pick["sharpe"],
                        "Robustness": pick["robustness"],
                        "Cost Efficiency": pick["cost_efficiency"],
                    })
        st.dataframe(pd.DataFrame(bank_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No parameter_bank.json yet — waiting for the first monthly "
                "advisor-training run (advisor_training.yml).")
else:
    st.warning("Waiting for data stream structure. Make sure your repository has executed a successful update.")