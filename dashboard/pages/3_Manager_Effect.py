"""
dashboard/pages/3_Manager_Effect.py
────────────────────────────────────
Manager Effect Analysis — Rolling 12m team attrition vs peer benchmark.
Only managers with team_size >= 5 shown (k-anonymity).
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Manager Effect | PeopleLens", page_icon="👔", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("👔 Manager Effect Analysis")
st.caption("Rolling 12-Month Team Attrition · Peer Benchmark · Wilson CI · k-anonymity (k≥5 per team)")
st.divider()


@st.cache_data(ttl=300)
def load_data():
    emp_path = ROOT / "data" / "synthetic" / "employees.csv"
    mgr_path = ROOT / "data" / "synthetic" / "managers.csv"
    if not emp_path.exists():
        return None, None
    employees = pd.read_csv(emp_path, parse_dates=["join_date", "exit_date"])
    managers = pd.read_csv(mgr_path) if mgr_path.exists() else pd.DataFrame()
    return employees, managers


employees, managers = load_data()
if employees is None:
    st.error("⚠️ No data. Run `python data_generator/generate_dataset.py`")
    st.stop()

from analytics.manager_effect import compute_manager_attrition

mgr_data = compute_manager_attrition(employees, managers)

if mgr_data.empty:
    st.warning("No manager data available with sufficient team sizes.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    depts = ["All"] + sorted(mgr_data["department"].dropna().unique().tolist())
    selected_dept = st.selectbox("Filter by Department", depts)
with col_f2:
    show_flagged = st.checkbox("Show flagged managers only", value=False)

filtered = mgr_data.copy()
if selected_dept != "All":
    filtered = filtered[filtered["department"] == selected_dept]
if show_flagged:
    filtered = filtered[filtered["risk_flag"] == True]

# ── Summary Metrics ────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Managers Analysed", len(mgr_data))
c2.metric("Flagged (>10pp above peers)", int(mgr_data["risk_flag"].sum()),
          delta=f"{mgr_data['risk_flag'].mean():.0%} of total")
c3.metric("Avg Team Attrition", f"{mgr_data['attrition_rate'].mean():.1%}")

st.divider()

# ── Manager Rankings Chart ─────────────────────────────────────────────────────
st.subheader("Manager Attrition vs Peer Benchmark")

top_n = min(25, len(filtered))
chart_data = filtered.head(top_n).copy()
chart_data["manager_label"] = chart_data["manager_id"].str[-6:]
chart_data["flag_color"] = chart_data["risk_flag"].map({True: "#FF5050", False: "#7C83FF"})

fig = go.Figure()
# Peer average line (per manager row)
fig.add_trace(go.Scatter(
    x=chart_data["manager_label"],
    y=chart_data["peer_avg_attrition"],
    mode="markers+lines",
    name="Peer Average",
    line=dict(color="#FFA500", dash="dash", width=2),
    marker=dict(size=6, color="#FFA500"),
))
# Actual attrition bars
fig.add_trace(go.Bar(
    x=chart_data["manager_label"],
    y=chart_data["attrition_rate"],
    name="Manager's Team",
    marker_color=chart_data["flag_color"],
    error_y=dict(
        type="data",
        array=(chart_data["ci_upper"] - chart_data["attrition_rate"]).tolist(),
        arrayminus=(chart_data["attrition_rate"] - chart_data["ci_lower"]).tolist(),
        visible=True,
        color="#888",
    ),
))
fig.update_layout(
    barmode="overlay",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#E0E0FF",
    height=450,
    yaxis=dict(tickformat=".0%", gridcolor="#2D3050", title="Attrition Rate"),
    xaxis=dict(title="Manager (last 6 chars of ID)", gridcolor="#2D3050"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=20, b=40),
)
st.plotly_chart(fig, use_container_width=True)
st.caption("🔴 Red bars = flagged managers (team attrition >10pp above peers). Error bars = 95% Wilson CI.")

st.divider()

# ── Data Table ─────────────────────────────────────────────────────────────────
st.subheader("Manager Details")
display_cols = ["manager_id", "department", "location", "team_size", "attrition_rate",
                "peer_avg_attrition", "attrition_vs_peers", "risk_flag"]
display_cols = [c for c in display_cols if c in filtered.columns]

styled = filtered[display_cols].head(50).style.format({
    "attrition_rate": "{:.1%}",
    "peer_avg_attrition": "{:.1%}",
    "attrition_vs_peers": "{:+.1%}",
}).applymap(lambda x: "background-color: rgba(255,80,80,0.2)" if x is True else "", subset=["risk_flag"])

st.dataframe(styled, use_container_width=True, height=400)
