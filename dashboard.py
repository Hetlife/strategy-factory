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
    import agents.researcher.researcher as researcher
    from agents.risk_manager.risk_manager import (
        sector_concentration, aggregate_real_money_exposure,
        portfolio_drawdown_correlation_flag,
    )
    from agents.master_trader.master_trader import recommend as master_trader_recommend
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

# --- MODERN / "APPLE-LIKE" STYLING ---
# Het, 2026-08-26: "I want the home interface to look more apple like and
# modern... make it like my portfolio so I know if my agents are making
# money." Streamlit's own chrome (default st.metric, st.container) is
# functional but plain -- this CSS block restyles just the portfolio hero
# below into rounded, shadowed cards with a system-font stack, without
# touching Streamlit's actual widget behavior underneath.
st.markdown("""
<style>
  html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
      "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  .portfolio-card {
    background: linear-gradient(165deg, #1c2333 0%, #12151f 100%);
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 18px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    border: 1px solid rgba(255,255,255,0.06);
  }
  .portfolio-label {
    font-size: 13px; font-weight: 600; letter-spacing: 0.4px;
    color: rgba(255,255,255,0.55); text-transform: uppercase; margin-bottom: 6px;
  }
  .portfolio-total { font-size: 44px; font-weight: 700; color: #f5f5f7;
    letter-spacing: -0.5px; line-height: 1.1; }
  .portfolio-change { font-size: 18px; font-weight: 600; margin-top: 4px; }
  .portfolio-change.up { color: #30d158; }
  .portfolio-change.down { color: #ff453a; }
  .portfolio-subrow { display: flex; gap: 28px; margin-top: 22px;
    flex-wrap: wrap; }
  .portfolio-stat .k { font-size: 12px; color: rgba(255,255,255,0.45);
    text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 2px; }
  .portfolio-stat .v { font-size: 20px; font-weight: 600; color: #f5f5f7; }
  .real-money-badge {
    display: inline-block; margin-top: 18px; padding: 6px 12px;
    background: rgba(255,159,10,0.12); border: 1px solid rgba(255,159,10,0.3);
    border-radius: 10px; font-size: 13px; color: #ff9f0a; font-weight: 600;
  }
  .status-pill { display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 20px; font-size: 13px; font-weight: 600;
    background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.75); }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; }
</style>
""", unsafe_allow_html=True)

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

@st.cache_data(ttl=60)
def _fetch_text(path, ts):
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/refs/heads/{BRANCH}/{path}?t={ts}"
    try:
        response = requests.get(url)
        return response.text if response.status_code == 200 else None
    except Exception:
        return None

def _run_health_check(ledger_data, state_data):
    """Shared by the heartbeat banner and the Office/Healer card -- runs the
    same tools/health_check.py deterministic checks against whatever was
    just fetched from GitHub, no separate local state needed."""
    if not (ledger_data and state_data):
        return None
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_tmp = os.path.join(tmpdir, "ledger.json")
        state_tmp = os.path.join(tmpdir, "state.json")
        _json.dump(ledger_data, open(ledger_tmp, "w"))
        _json.dump(state_data, open(state_tmp, "w"))
        try:
            from tools import health_check
            return health_check.run_all(ledger_tmp, state_tmp)
        except Exception:
            return None

# --- LOAD DATA ---
current_timestamp = int(time.time())
data = load_ledger_data(current_timestamp)
advisor_state = load_advisor_state(current_timestamp)
parameter_bank = load_parameter_bank(current_timestamp)
state_json = load_state_json(current_timestamp)
log_text = _fetch_text("AUTONOMOUS_LOG.md", current_timestamp)
hr_log_text = _fetch_text(".autonomous/hr_log.md", current_timestamp)

def _relative_days(date_str):
    """AUTONOMOUS_LOG.md and ledger.json only record day-level dates (no
    time-of-day), so this can only ever be honest down to a day -- 'X
    minutes ago' would be fabricated precision the underlying data doesn't
    have. 'today'/'Nd ago' is the truthful version of the same idea."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return date_str
    delta = (datetime.now(timezone.utc).date() - d).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "yesterday"
    return f"{delta}d ago"

_page_loaded_at = datetime.now(timezone.utc)

# ======================================================= PORTFOLIO HERO ===
# Het, 2026-08-26: "make it like my portfolio so I know if my agents are
# making money or [losing], how much is invested, total profit or loss."
# Computed from real ledger.json equities -- every number here is PAPER
# (simulated), never real money; that distinction is the single most
# important thing on this page not to blur, so it's stated explicitly,
# not just implied by a caption someone might skip.
if data and "contestants" in data:
    con = data["contestants"]
    reg = data.get("registry", {})
    live = {n: s for n, s in con.items()
            if not s.get("retired") and not reg.get(n, {}).get("permanent")}
    n_live = len(live)
    total_paper_capital = n_live * PAPER_STARTING_CAPITAL
    total_paper_pnl = sum((s.get("equity", 1.0) - 1.0) * PAPER_STARTING_CAPITAL
                          for s in live.values())
    total_paper_pct = (total_paper_pnl / total_paper_capital * 100) if total_paper_capital else 0.0

    bench = next((s for n, s in con.items() if reg.get(n, {}).get("permanent")), None)
    bench_pct = (bench.get("equity", 1.0) - 1.0) * 100 if bench else None

    last_dates = [s["history"][-1][0] for s in con.values() if s.get("history")]
    last_update_str = max(last_dates) if last_dates else None
    days_stale = ((datetime.now(timezone.utc).date()
                   - datetime.strptime(last_update_str, "%Y-%m-%d").date()).days
                  if last_update_str else None)
    findings = _run_health_check(data, state_json)
    real_findings = [f for f in (findings or []) if f[0] != "info"]
    is_online = (days_stale is not None and days_stale <= 3
                 and not any(f[0] == "error" for f in real_findings))

    change_cls = "up" if total_paper_pnl >= 0 else "down"
    change_sign = "+" if total_paper_pnl >= 0 else ""
    status_color = "#30d158" if is_online else "#ff453a"
    status_text = "System online" if is_online else "System offline"
    vs_bench = ""
    if bench_pct is not None:
        diff = total_paper_pct - bench_pct
        vs_bench = (f'<div class="portfolio-stat"><div class="k">vs Nifty benchmark</div>'
                    f'<div class="v">{"+" if diff >= 0 else ""}{diff:.2f}pp</div></div>')

    health_html = "✅ Clear" if not real_findings else f"⚠️ {len(real_findings)} finding(s)"
    updated_str = _relative_days(last_update_str) if last_update_str else "unknown"
    # Built as ONE unindented line, not a multi-line indented f-string:
    # Streamlit's markdown parser treats any line with 4+ leading spaces
    # as an indented code block (a real CommonMark rule, not a bug) --
    # a naturally-indented multi-line f-string trips it silently, which
    # is exactly what happened here the first time (verified via the
    # actual rendered DOM, not guessed).
    portfolio_html = (
        '<div class="portfolio-card">'
        f'<div class="status-pill"><span class="status-dot" style="background:{status_color}"></span>'
        f'{status_text} &middot; updated {updated_str}</div>'
        f'<div class="portfolio-label" style="margin-top:16px;">Total paper P&amp;L &middot; {n_live} active agents</div>'
        f'<div class="portfolio-total">{change_sign}Rs {total_paper_pnl:,.0f}</div>'
        f'<div class="portfolio-change {change_cls}">{change_sign}{total_paper_pct:.2f}%</div>'
        '<div class="portfolio-subrow">'
        f'<div class="portfolio-stat"><div class="k">Paper capital at play</div><div class="v">Rs {total_paper_capital:,.0f}</div></div>'
        f'{vs_bench}'
        f'<div class="portfolio-stat"><div class="k">Health</div><div class="v">{health_html}</div></div>'
        '</div>'
        '<div class="real-money-badge">⚠️ All figures above are PAPER / simulated — real capital invested: Rs 0</div>'
        '</div>'
    )
    st.markdown(portfolio_html, unsafe_allow_html=True)
else:
    st.warning("Waiting on ledger data to build the portfolio view — see the Arena tab.")

with st.expander("🕘 Recent AI activity"):
    st.caption(f"Data on this page refreshed {int((datetime.now(timezone.utc) - _page_loaded_at).total_seconds())}s ago "
              "(cached up to 60s at a time — hit Refresh in the sidebar for the latest).")
    if log_text:
        lines = [l for l in log_text.strip().splitlines()
                 if l.startswith("2")]  # skip header/blank lines
        recent = lines[-10:][::-1]
        for line in recent:
            parts = line.split("|", 4)
            if len(parts) >= 5:
                date, commit, qid, outcome, note = [p.strip() for p in parts]
                note = note if len(note) <= 160 else note[:157] + "..."
                st.caption(f"**{_relative_days(date)}** ({date}) · {qid} · {outcome} — {note}")
            else:
                st.caption(line.strip())
    else:
        st.caption("AUTONOMOUS_LOG.md not fetched.")

tab_arena, tab_office = st.tabs(["📊 Arena", "🏢 The Office"])

# ============================================================ ARENA TAB ===
with tab_arena:
    if data and "contestants" in data:
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

        # Active-count and total-P&L already live in the portfolio hero above
        # the tabs -- this row only adds what that hero doesn't cover
        # (per-contestant detail: who's on top, how many have been retired).
        st.subheader("📈 Strategy Performance")
        col1, col2 = st.columns(2)
        col1.metric("Contestants", total_strategies,
                    f"{total_strategies - active_strategies} retired" if total_strategies > active_strategies else None,
                    delta_color="off")
        if metric_cards_data:
            _live_rows = [r for r in metric_cards_data if r["Status"] == "Active"]
            if _live_rows:
                _best = max(_live_rows, key=lambda r: r["Current Equity"])
                _best_pct = (_best["Current Equity"] - 1) * 100
                col2.metric("Top Performer", _best["Strategy"],
                            f"{_best_pct:+.2f}%",
                            help="The live contestant with the highest equity right "
                                 "now, and how far it's moved since it started (not "
                                 "a Rs figure -- every contestant starts at the same "
                                 f"Rs {PAPER_STARTING_CAPITAL:,} paper baseline, so % "
                                 "move is what actually differs between them).")
            else:
                col2.metric("Top Performer", "—")
        else:
            col2.metric("Top Performer", "—")

        st.markdown("---")
        st.subheader("📈 Equity Growth")
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
        desk7, desk8, _sp3 = st.columns(3)

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
            grave = researcher.graveyard(data)
            if grave:
                with st.expander(f"🪦 Graveyard — {len(grave)} setup(s) already tried and failed"):
                    st.caption(
                        "The shared 'what not to do' record every evolution "
                        "round checks before proposing a new candidate — an "
                        "exact repeat of one of these gets skipped "
                        "automatically. Never used to invent new hypotheses, "
                        "only to avoid repeating a proven failure."
                    )
                    for entry in grave:
                        st.write(f"**{entry['name']}** ({entry['fn']}/{entry['sector']}) "
                                f"— {entry['numeric_params']}, survived "
                                f"{entry['days_survived']} days, final equity "
                                f"{entry['final_equity']} — {entry['cause']}")
            else:
                st.caption("Graveyard is empty — nothing has been retired yet.")

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
                findings = _run_health_check(data, state_json)
                if findings is None:
                    st.caption("(couldn't run tools/health_check.py)")
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

        # --- HR ---
        with desk7:
            st.markdown("### 🗂️ HR")
            st.caption("Hires new team-role helper agents when there's a "
                       "real gap — never trading strategies, never runs "
                       "unsupervised. See agents/hr/hr.py.")
            if hr_log_text:
                hired = hr_log_text.count("\n- HIRED |")
                st.info(f"{hired} / 10 pre-authorized hires used.")
                lines = [l for l in hr_log_text.strip().splitlines()
                         if l.startswith("- HIRED") or l.startswith("- PROPOSED")]
                if lines:
                    with st.expander("Hiring history"):
                        for l in lines[-10:]:
                            st.write(l.lstrip("- "))
                else:
                    st.caption("No hires yet — built and ready, waiting on a "
                              "real observed gap before scaffolding anything.")
            else:
                st.caption(".autonomous/hr_log.md not fetched.")

        # --- Master Trader ---
        with desk8:
            st.markdown("### 🧑‍💼 Master Trader")
            st.caption("Synthesizes Judge/Risk Manager/Researcher into one "
                       "read -- an advisory recommendation, not a trading "
                       "result. Never distributes capital, never trades: "
                       "real-money exposure across every strategy is Rs 0, "
                       "same as every other number on this page.")
            try:
                rec = master_trader_recommend(data)
                if rec["eligible_for_promotion"]:
                    st.success(f"{len(rec['eligible_for_promotion'])} "
                              f"strategy(ies) mechanically clear every "
                              f"PROMOTE threshold right now.")
                else:
                    st.info("Nobody currently clears every PROMOTE "
                           "threshold -- normal, not a problem.")
                st.metric("Real-money exposure", f"Rs {rec['real_money_exposure']:,}")
                if rec["correlated_drawdown_flag"]:
                    st.warning("Correlated drawdown flagged -- see Risk "
                              "Manager for detail.")
                if rec["graveyard_size"]:
                    st.caption(f"{rec['graveyard_size']} setup(s) already "
                              f"tried and retired -- evolution avoids exact "
                              f"repeats of these automatically.")
            except Exception as e:
                st.caption(f"(couldn't run master_trader.recommend(): {e})")

    st.markdown("---")
    st.subheader("📋 Notes")
    st.warning(
        "⚠️ **This does NOT reach Claude, even though the save succeeds.** "
        "It writes to this page's own disk (`.autonomous/dashboard_notes.md`), "
        "which — on a hosted copy like Streamlit Community Cloud — is a "
        "throwaway container filesystem, not this GitHub repo. It's never "
        "committed, so no Claude session will ever see it, no matter how "
        "many times you save. **Use the note bowl in the Trading Floor "
        "artifact instead** — that one actually persists and Claude can "
        "read it back. This box only makes sense if you're running "
        "`dashboard.py` on your own machine AND manually `git add`/`commit`/"
        "`push` the notes file afterward."
    )
    note_text = st.text_area("Write a note or question to bring back later:", height=100)
    if st.button("Save note"):
        if note_text.strip():
            try:
                os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                with open(NOTES_FILE, "a") as f:
                    f.write(f"\n- **{timestamp}** — {note_text.strip()}\n")
                st.success(f"Written to {NOTES_FILE} on this page's own disk. "
                          f"Remember: Claude can't see this until you commit+push "
                          f"it yourself — it is NOT the same as the Trading Floor "
                          f"artifact's note bowl.")
            except Exception as e:
                st.error(f"Couldn't save (read-only filesystem?): {e}")
        else:
            st.warning("Nothing to save — write something first.")

    if os.path.exists(NOTES_FILE):
        with st.expander("Previously saved notes"):
            st.markdown(open(NOTES_FILE).read())
