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

st.set_page_config(page_title="Strategy Factory Arena", layout="wide", page_icon="🤖")

# --- SIDEBAR & REFRESH BUTTON ---
st.sidebar.title("🔄 Controls")

if st.sidebar.button("Refresh Data Now"):
    st.cache_data.clear()
    st.toast("Fetching latest data from GitHub...", icon="⏳")
    time.sleep(1)
    st.rerun()

# --- CACHED DATA LOADER ---
@st.cache_data(ttl=60)
def load_ledger_data(ts):
    # Fixed complete raw URL path structure
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/refs/heads/{BRANCH}/{FILE_PATH}?t={ts}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data from GitHub. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- LOAD DATA ---
current_timestamp = int(time.time())
data = load_ledger_data(current_timestamp)

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
            
            metric_cards_data.append({
                "Strategy": name,
                "Current Equity": config.get("equity", 1.0),
                "Peak Equity": config.get("peak", 1.0),
                "Trades Executed": config.get("trades", 0),
                "Days in Market": config.get("days_in_market", 0),
                "Status": "Retired" if config.get("retired", False) else "Active"
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
else:
    st.warning("Waiting for data stream structure. Make sure your repository has executed a successful update.")