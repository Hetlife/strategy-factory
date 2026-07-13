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

# Clicking this button will clear the data cache and rerun the app
if st.sidebar.button("Refresh Data Now"):
    st.cache_data.clear()
    st.toast("Fetching latest data from GitHub...", icon="⏳")
    time.sleep(1) # Brief pause for visual feedback
    st.rerun()

# --- CACHED DATA LOADER ---
# We use a time-based parameter (ts) to force GitHub to bypass its CDN cache
@st.cache_data(ttl=60) # Automatically expires after 60 seconds anyway
def load_ledger_data(ts):
    # Appending a timestamp (?t=...) ensures we fetch a non-cached version from GitHub's servers
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
# Pass the current timestamp to bypass any caching layers
current_timestamp = int(time.time())
data = load_ledger_data(current_timestamp)

# ... (Keep the rest of your dashboard.py code exactly the same below this line) ...
if data and "contestants" in data:
    st.title("🤖 Strategy Factory Trading Arena")
    # [The rest of your existing plotting and table logic goes here]